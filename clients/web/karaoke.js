/**
 * ============================================================================
 * MEDIDOCX AI - KARAOKE TEXT HIGHLIGHTER ENGINE (v1.0)
 * ============================================================================
 * Tính năng trợ năng cao cấp cho người cao tuổi và người khó đọc (Dyslexia):
 * 1. Khối thông tin đang đọc được làm nổi bật (sáng viền vàng hổ phách).
 * 2. Câu đang đọc được tô vàng (ngắt câu ở dấu chấm / chấm hỏi / chấm than / xuống dòng).
 * 3. Tự động cuộn theo dòng đọc (Auto-scroll) trong văn bản dài.
 * 4. Tương thích 100% với toàn bộ file MP3 có sẵn và âm thanh sinh động.
 * ============================================================================
 */

// Ranh giới câu: sau . ! ? … (kèm ngoặc/nháy đóng) và có khoảng trắng phía sau
const SENTENCE_BREAK = /(?<=[.!?…]["”'’)\]]*)(\s+)/;
// Câu dài quá mức này (thiếu dấu chấm) -> chia tiếp ở dấu phẩy / chấm phẩy / hai chấm
const MAX_SENTENCE_CHARS = 300;
const CLAUSE_BREAK = /(?<=[,;:])(\s+)/;
// Chữ viết tắt có dấu chấm KHÔNG phải cuối câu ("TP. Hồ Chí Minh", "ThS. Lan"): không ngắt sau chúng
const ABBREVIATION_END = /(?:^|[\s(])(?:TP|Tp|TX|TT|Q|P|F|ThS|TS|PGS|GS|BS|BSCKI|BSCKII|KS|CN|Mr|Mrs|Ms|Dr|St|No)\.$/;

class KaraokeHighlighter {
    constructor(audioElement) {
        this.audio = audioElement;
        this.activeMode = null; // 'medicine_main' | 'medicine_warning' | 'document'
        this.timeline = [];     // Danh sách các mốc: [{ start, end, span, blockEl }]
        this.currentSpan = null;
        this.currentBlockEl = null;
        this.rafId = null;
        this.totalDuration = 0;

        this._bindAudioEvents();
    }

    _bindAudioEvents() {
        if (!this.audio) return;

        this.audio.addEventListener('play', () => {
            this._startLoop();
        });

        this.audio.addEventListener('pause', () => {
            this._stopLoop();
        });

        this.audio.addEventListener('ended', () => {
            this._stopLoop();
            this.reset();
        });

        // Hỗ trợ khi người dùng tua / click thanh thời gian
        this.audio.addEventListener('timeupdate', () => {
            if (this.audio.paused) {
                this.update(this.audio.currentTime, this.audio.duration);
            }
        });

        this.audio.addEventListener('loadedmetadata', () => {
            if (this.audio.duration && this.timeline.length > 0) {
                this._recalculateTimelineDuration(this.audio.duration);
            }
        });
    }

    _startLoop() {
        this._stopLoop();
        const tick = () => {
            if (this.audio && !this.audio.paused && !this.audio.ended) {
                this.update(this.audio.currentTime, this.audio.duration);
                this.rafId = requestAnimationFrame(tick);
            }
        };
        this.rafId = requestAnimationFrame(tick);
    }

    _stopLoop() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
    }

    /**
     * Tính toán trọng số thời gian của một từ dựa trên độ dài và dấu câu ngắt nghỉ.
     */
    _getWordWeight(word) {
        if (!word) return 0;
        const clean = word.trim();
        // Ký tự phân cách hoặc icon trang trí không phát âm -> Trọng số 0
        if (/^[•📌═\-—*#\d\W]+$/.test(clean) && !/[a-zA-ZÀ-ỹ0-9]/.test(clean)) {
            return 0;
        }
        // Dấu chấm câu, chấm than, hỏi: nghỉ nhịp dài hơn (~0.4s)
        if (/[.!?]$/.test(clean)) return 2.0;
        // Dấu phẩy, hai chấm, chấm phẩy: nghỉ nhịp vừa (~0.25s)
        if (/[,;:]$/.test(clean)) return 1.45;
        // Từ dài tiếng Việt / thuật ngữ y tế
        if (clean.length >= 7) return 1.3;
        // Từ ngắn 1-2 ký tự (và, có, 1, 2, mg...)
        if (clean.length <= 2) return 0.75;
        return 1.0;
    }

    /** Thời lượng ước tính của một câu = tổng trọng số các từ trong câu. */
    _getSentenceWeight(sentence) {
        return sentence.split(/\s+/).reduce((sum, w) => sum + this._getWordWeight(w), 0);
    }

    /**
     * Chia một dòng thành các câu: ngắt sau . ! ? … (có khoảng trắng phía sau, nên "1.5" hay
     * "2.500.000" không bị ngắt). Câu quá dài (văn bản thiếu dấu chấm) được chia tiếp ở , ; :
     * Trả về mảng xen kẽ [câu, khoảng trắng, câu, ...] để ghép lại vẫn đúng nguyên văn.
     */
    _splitLineIntoSentences(line) {
        const parts = this._rejoinAbbreviations(line.split(SENTENCE_BREAK));
        return parts.flatMap((part) =>
            part.trim() && part.length > MAX_SENTENCE_CHARS ? this._splitLongSentence(part) : [part]
        );
    }

    /** Câu quá dài: chia ở , ; : rồi gom các vế lại thành cụm ~MAX_SENTENCE_CHARS/2 (không vụn từng vế). */
    _splitLongSentence(sentence) {
        const target = MAX_SENTENCE_CHARS / 2;
        const pieces = sentence.split(CLAUSE_BREAK); // [vế, khoảng trắng, vế, ...]
        const out = [pieces[0]];
        for (let i = 1; i < pieces.length; i += 2) {
            const [space, clause] = [pieces[i], pieces[i + 1] ?? ''];
            if (out[out.length - 1].length + space.length + clause.length <= target) {
                out[out.length - 1] += space + clause;
            } else {
                out.push(space, clause);
            }
        }
        return out;
    }

    /** Ghép lại các chỗ bị ngắt nhầm sau chữ viết tắt. parts = [câu, khoảng trắng, câu, ...] */
    _rejoinAbbreviations(parts) {
        const out = [];
        for (let i = 0; i < parts.length; i++) {
            const last = out.length - 1;
            if (i % 2 === 0 && last >= 1 && ABBREVIATION_END.test(out[last - 1])) {
                out[last - 1] += out.pop() + parts[i]; // câu trước + khoảng trắng + câu này
            } else {
                out.push(parts[i]);
            }
        }
        return out;
    }

    /**
     * Bọc văn bản trong element thành từng câu <span class="karaoke-sentence">.
     * Xuống dòng (tiêu đề, mục liệt kê) cũng là ranh giới câu. Giữ nguyên 100% chữ và xuống dòng.
     * @returns {Array<{span: HTMLElement, text: string, weight: number}>}
     */
    _wrapSentences(element) {
        if (!element) return [];

        const text = element.innerText || element.textContent || '';
        if (!text.trim()) return [];

        const html = text.split(/(\n)/).map((line) => {
            if (line === '\n') return line;
            return this._splitLineIntoSentences(line).map((part) => {
                if (!part.trim()) return part; // khoảng trắng giữa các câu
                const weight = this._getSentenceWeight(part);
                const cls = weight > 0 ? 'karaoke-sentence' : 'karaoke-symbol';
                return `<span class="${cls}" data-weight="${weight}">${this._escapeHtml(part)}</span>`;
            }).join('');
        }).join('');

        element.innerHTML = html;

        return [...element.querySelectorAll('.karaoke-sentence')].map((span) => ({
            span,
            text: span.textContent,
            weight: parseFloat(span.dataset.weight) || 1.0,
        }));
    }

    _escapeHtml(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    /**
     * Xây dựng timeline đồng bộ giữa danh sách sections và thời lượng audio.
     */
    _buildTimeline(sections, duration) {
        this.timeline = [];
        this.totalDuration = duration || 0;

        let totalWeight = 0;
        const allItems = [];

        sections.forEach(sec => {
            // 1. Các từ dẫn âm thanh (prefix words mà giọng đọc phát trước khi đọc nội dung)
            if (sec.prefixWords && sec.prefixWords.length > 0) {
                sec.prefixWords.forEach(pw => {
                    const w = this._getWordWeight(pw);
                    totalWeight += w;
                    allItems.push({
                        type: 'prefix',
                        weight: w,
                        blockEl: sec.blockEl,
                        span: null
                    });
                });
            }

            // 2. Các câu hiển thị thực tế trên giao diện
            if (sec.items && sec.items.length > 0) {
                sec.items.forEach(wObj => {
                    if (wObj.weight <= 0) return;
                    totalWeight += wObj.weight;
                    allItems.push({
                        type: 'content',
                        weight: wObj.weight,
                        blockEl: sec.blockEl,
                        span: wObj.span
                    });
                });
            }
        });

        if (totalWeight <= 0) return;

        // Phân bổ thời gian theo tỷ trọng
        let cumWeight = 0;
        allItems.forEach(item => {
            const startRatio = cumWeight / totalWeight;
            cumWeight += item.weight;
            const endRatio = cumWeight / totalWeight;

            this.timeline.push({
                startRatio,
                endRatio,
                start: duration ? startRatio * duration : 0,
                end: duration ? endRatio * duration : 0,
                span: item.span,
                blockEl: item.blockEl
            });
        });
    }

    _recalculateTimelineDuration(duration) {
        if (!duration || duration <= 0 || !isFinite(duration)) return;
        this.totalDuration = duration;
        this.timeline.forEach(item => {
            item.start = item.startRatio * duration;
            item.end = item.endRatio * duration;
        });
    }

    // ========================================================================
    // 1. CHẾ ĐỘ THUỐC: ÂM THANH CHÍNH (TÊN, CÔNG DỤNG, CÁCH DÙNG, LIỀU DÙNG)
    // ========================================================================
    prepareMedicineMain() {
        this.reset();
        this.activeMode = 'medicine_main';

        const titleBlock = document.querySelector('.card-medicine-title');
        const titleEl = document.getElementById('lblTenThuoc');

        const indBlock = document.querySelector('.block-indication');
        const indEl = document.getElementById('lblCongDung');

        const dosageBlock = document.querySelector('.block-dosage');
        const timingEl = document.getElementById('lblThoiDiem');
        const adultEl = document.getElementById('lblLieuNguoiLon');
        const childEl = document.getElementById('lblLieuTreEm');

        const badgeEl = document.getElementById('result-badge');
        const isAI = badgeEl && (badgeEl.classList.contains('badge-ai') || badgeEl.innerText.includes('AI'));

        const sections = [];

        // Nếu là thuốc nhận diện bằng AI -> Có câu khuyến cáo mở đầu khớp 100% từng từ với giọng đọc TTS
        if (isAI && badgeEl) {
            sections.push({
                prefixWords: "Thông tin trên được tra cứu bằng AI, có thể sai sót, thông tin này chỉ mang tính chất tham khảo, mọi cân nhắc xin vui lòng liên hệ bác sĩ hoặc dược sĩ.".split(/\s+/),
                blockEl: badgeEl,
                items: []
            });
        }

        // 1. Tên thuốc
        if (titleEl && titleEl.innerText.trim()) {
            sections.push({
                prefixWords: ["Tên", "thuốc:"],
                blockEl: titleBlock,
                items: this._wrapSentences(titleEl)
            });
        }

        // 2. Công dụng
        if (indEl && indEl.innerText.trim()) {
            sections.push({
                prefixWords: ["Công", "dụng:"],
                blockEl: indBlock,
                items: this._wrapSentences(indEl)
            });
        }

        // 3. Cách dùng / Thời điểm uống (chỉ đọc riêng nếu chưa có trong liều người lớn)
        const timingText = timingEl ? timingEl.innerText.trim() : '';
        const adultText = adultEl ? adultEl.innerText.trim() : '';
        const hasTiming = timingText && timingText !== "Chưa có thông tin" && !adultText.toLowerCase().includes(timingText.toLowerCase());

        if (hasTiming) {
            sections.push({
                prefixWords: ["Cách", "dùng:"],
                blockEl: dosageBlock,
                items: this._wrapSentences(timingEl)
            });
        }

        // 4. Liều người lớn
        if (adultEl && adultEl.innerText.trim()) {
            sections.push({
                prefixWords: ["Liều", "dùng", "cho", "người", "lớn:"],
                blockEl: dosageBlock,
                items: this._wrapSentences(adultEl)
            });
        }

        // 5. Liều trẻ em
        const childText = childEl ? childEl.innerText.trim() : '';
        const hasChild = childText && !['chưa rõ', 'chưa có thông tin', 'không rõ'].some(k => childText.toLowerCase().includes(k));

        if (hasChild) {
            sections.push({
                prefixWords: ["Liều", "dùng", "cho", "trẻ", "em:"],
                blockEl: dosageBlock,
                items: this._wrapSentences(childEl)
            });
        }

        const duration = this.audio && !isNaN(this.audio.duration) ? this.audio.duration : 0;
        this._buildTimeline(sections, duration);
    }

    // ========================================================================
    // 2. CHẾ ĐỘ THUỐC: ÂM THANH LƯU Ý / CẢNH BÁO ĐẶC BIỆT
    // ========================================================================
    prepareMedicineWarning() {
        this.reset();
        this.activeMode = 'medicine_warning';

        const warnBlock = document.querySelector('.block-warning');
        const warnEl = document.getElementById('lblLuuYChiTiet');
        const titleEl = document.getElementById('lblTenThuoc');
        const drugName = titleEl ? titleEl.innerText.trim() : "";

        const prefix = ["Lưu", "ý", "quan", "trọng", "khi", "sử", "dụng", "thuốc"];
        if (drugName) {
            prefix.push(drugName + ":");
        }

        const sections = [{
            prefixWords: prefix,
            blockEl: warnBlock,
            items: this._wrapSentences(warnEl)
        }];

        const duration = this.audio && !isNaN(this.audio.duration) ? this.audio.duration : 0;
        this._buildTimeline(sections, duration);
    }

    // ========================================================================
    // 3. CHẾ ĐỘ VĂN BẢN (DYSLEXIA READER - TOÀN VĂN & TÓM TẮT Ý CHÍNH)
    // ========================================================================
    prepareDocument() {
        this.reset();
        this.activeMode = 'document';

        const docBlock = document.querySelector('.doc-readable-container');
        const docEl = document.getElementById('lblDocContent');

        if (!docEl) return;

        const sections = [{
            prefixWords: [],
            blockEl: docBlock,
            items: this._wrapSentences(docEl)
        }];

        const duration = this.audio && !isNaN(this.audio.duration) ? this.audio.duration : 0;
        this._buildTimeline(sections, duration);
    }

    /**
     * Bọc sẵn toàn bộ câu trong phần tử văn bản thành <span class="karaoke-sentence">
     * @param {HTMLElement} docEl
     * @returns {Array<{span: HTMLElement, text: string, weight: number}>}
     */
    wrapDocumentSentences(docEl) {
        if (!docEl) return [];
        return this._wrapSentences(docEl);
    }

    /**
     * Tô sáng câu đang phát trong SentenceAudioQueue (mỗi đoạn âm thanh = đúng 1 câu,
     * nên câu sáng lên đúng lúc giọng đọc bắt đầu và tắt khi đọc xong, không phải ước lượng).
     * @param {Array<{span: HTMLElement, text: string, weight: number}>} sentenceItems
     * @param {number} duration
     */
    prepareDocumentChunk(sentenceItems, duration) {
        this._stopLoop();
        this.activeMode = 'document';

        // Đánh dấu câu trước thành 'past' (đã đọc xong)
        if (this.currentSpan) {
            this.currentSpan.classList.remove('active');
            this.currentSpan.classList.add('past');
            this.currentSpan = null;
        }

        const docBlock = document.querySelector('.doc-readable-container');
        if (docBlock) {
            docBlock.classList.add('karaoke-active-block');
            this.currentBlockEl = docBlock;
        }

        const sections = [{
            prefixWords: [],
            blockEl: docBlock,
            items: sentenceItems || []
        }];

        this._buildTimeline(sections, duration || 0);
        this._startLoop();
    }

    // ========================================================================
    // CẬP NHẬT TRẠNG THÁI HIGHLIGHT (CHẠY 60FPS QUA REQUESTANIMATIONFRAME)
    // ========================================================================
    update(currentTime, duration) {
        if (!this.timeline || this.timeline.length === 0) return;

        // Nếu duration vừa nạp xong
        if (duration && duration > 0 && isFinite(duration) && Math.abs(this.totalDuration - duration) > 0.1) {
            this._recalculateTimelineDuration(duration);
        }

        const effectiveDuration = (duration && isFinite(duration) && duration > 0) ? duration : this.totalDuration;
        if (!effectiveDuration || effectiveDuration <= 0 || !isFinite(effectiveDuration)) return;

        // Tìm mốc thời gian khớp với currentTime
        let activeEntry = null;
        for (let i = 0; i < this.timeline.length; i++) {
            const entry = this.timeline[i];
            if (currentTime >= entry.start && currentTime < entry.end) {
                activeEntry = entry;
                break;
            }
        }

        // Nếu đã đọc đến những tích tắc cuối
        if (!activeEntry && currentTime >= this.timeline[this.timeline.length - 1].end) {
            activeEntry = this.timeline[this.timeline.length - 1];
        }

        // 1. Cập nhật sáng viền khối thông tin (Block Highlighting)
        const targetBlock = activeEntry ? activeEntry.blockEl : null;
        if (this.currentBlockEl !== targetBlock) {
            if (this.currentBlockEl) {
                this.currentBlockEl.classList.remove('karaoke-active-block');
            }
            if (targetBlock) {
                targetBlock.classList.add('karaoke-active-block');
            }
            this.currentBlockEl = targetBlock;
        }

        // 2. Cập nhật tô vàng câu đang đọc (Sentence Highlighting)
        const targetSpan = activeEntry ? activeEntry.span : null;
        if (this.currentSpan !== targetSpan) {
            if (this.currentSpan) {
                this.currentSpan.classList.remove('active');
                this.currentSpan.classList.add('past');
            }
            if (targetSpan) {
                targetSpan.classList.add('active');
                targetSpan.classList.remove('past');

                // Tự động cuộn theo câu trong văn bản dài
                if (this.activeMode === 'document') {
                    this._scrollSentenceIntoView(targetSpan);
                }
            }
            this.currentSpan = targetSpan;
        }
    }

    _scrollSentenceIntoView(span) {
        if (!span) return;
        const container = document.querySelector('.doc-readable-container');
        if (!container) return;

        const cRect = container.getBoundingClientRect();
        const sRect = span.getBoundingClientRect();

        // Nếu câu đang đọc lệch khỏi vùng quan sát
        if (sRect.top < cRect.top + 45 || sRect.bottom > cRect.bottom - 45) {
            span.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
        }
    }

    /**
     * Dọn sạch toàn bộ trạng thái tô vàng, đưa giao diện về ban đầu.
     */
    reset() {
        this._stopLoop();

        if (this.currentBlockEl) {
            this.currentBlockEl.classList.remove('karaoke-active-block');
            this.currentBlockEl = null;
        }

        // Xóa class active và past trên tất cả các khối
        document.querySelectorAll('.karaoke-active-block').forEach(el => {
            el.classList.remove('karaoke-active-block');
        });

        document.querySelectorAll('.karaoke-sentence.active, .karaoke-sentence.past').forEach(el => {
            el.classList.remove('active', 'past');
        });

        this.timeline = [];
        this.currentSpan = null;
    }
}

// Khởi tạo đối tượng toàn cục (cho Browser và Module)
if (typeof window !== 'undefined') {
    window.KaraokeHighlighter = KaraokeHighlighter;
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KaraokeHighlighter;
}
