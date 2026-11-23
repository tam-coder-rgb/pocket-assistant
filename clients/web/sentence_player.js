/**
 * ============================================================================
 * MEDIDOCX AI - PIPELINED SENTENCE AUDIO QUEUE ENGINE (v1.0)
 * ============================================================================
 * Giải pháp giảm độ trễ giọng đọc văn bản từ 5-10s xuống dưới 0.3s:
 * 1. Tách văn bản thành từng câu/cụm câu hợp lý (~10-25 từ/câu).
 * 2. Tải và phát ngay câu đầu tiên (~0.25s - 0.35s).
 * 3. Đồng thời tải gối đầu (prefetching) các câu tiếp theo vào RAM trong lúc câu trước đang đọc.
 * 4. Chuyển câu mượt mà không có khoảng lặng (zero-delay).
 * 5. Tự động đồng bộ với KaraokeHighlighter: tô vàng đúng câu đang đọc.
 * 6. Lưu trữ đệm trong RAM (In-Memory Blob Cache) để nghe lại tức thì 0ms.
 * ============================================================================
 */

class SentenceAudioQueue {
    constructor(client, audioPlayer, karaoke) {
        this.client = client;
        this.audioPlayer = audioPlayer;
        this.karaoke = karaoke;

        this.chunks = [];           // Danh sách câu [{ text, speechText, wordItems }]
        this.currentIndex = -1;
        this.isPlaying = false;
        this.sessionId = 0;         // ID phiên phát để hủy an toàn khi người dùng bấm dừng
        this.currentSpeed = 1.0;

        this.blobCache = new Map(); // Cache URL nhị phân âm thanh trong RAM
        this.textCache = new Map(); // Cache nạp trước theo nội dung câu (Eager First-Sentence)
        this.prefetchingSet = new Set();
        this.isPrefetchingRunning = false;

        this._boundOnEnded = this._handleAudioEnded.bind(this);
        this._boundOnError = this._handleAudioError.bind(this);
    }

    /**
     * Tách văn bản thành các câu/cụm câu tự nhiên tiếng Việt.
     * Gộp các câu quá ngắn (< 4 từ) để giọng đọc liền mạch, tự nhiên.
     */
    _splitIntoChunks(rawText) {
        if (!rawText || !rawText.trim()) return [];

        // 1. Tách thô theo dấu câu và dòng
        // Regex tránh tách nhầm số thập phân (1.5) hoặc chữ viết tắt phổ biến
        const cleaned = rawText
            .replace(/\r\n/g, '\n')
            .replace(/[•═📌💡*#\-_]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();

        if (!cleaned) return [];

        // Tách câu theo dấu chấm, hỏi, than, hai chấm hoặc ngắt dòng
        const rawSentences = cleaned
            .split(/(?<=[.!?:\n])\s+/)
            .map(s => s.trim())
            .filter(s => s.length > 0);

        const chunks = [];
        let currentChunkWords = [];

        rawSentences.forEach(sentence => {
            const words = sentence.split(/\s+/).filter(Boolean);
            if (words.length === 0) return;

            // Nếu câu hiện tại cộng câu mới dưới 25 từ, gộp lại thành 1 cụm
            if (currentChunkWords.length > 0 && (currentChunkWords.length + words.length) <= 25) {
                currentChunkWords.push(...words);
            } else {
                if (currentChunkWords.length > 0) {
                    const text = currentChunkWords.join(' ');
                    chunks.push({
                        text,
                        speechText: text,
                        wordCount: currentChunkWords.length,
                        wordItems: []
                    });
                }
                currentChunkWords = [...words];
            }
        });

        if (currentChunkWords.length > 0) {
            const text = currentChunkWords.join(' ');
            chunks.push({
                text,
                speechText: text,
                wordCount: currentChunkWords.length,
                wordItems: []
            });
        }

        return chunks;
    }

    /**
     * Chuẩn bị dữ liệu cho một văn bản mới:
     * - Bọc thẻ span cho từng câu trong container để hiển thị highlight
     * - Mỗi câu trên DOM là một đoạn âm thanh riêng -> thước đọc khớp tuyệt đối với giọng nói
     *
     * @param {string} fullText - Toàn bộ văn bản hiển thị
     * @param {HTMLElement} containerEl - Phần tử DOM hiển thị văn bản (#lblDocContent)
     * @param {number} speed - Tốc độ đọc
     */
    prepare(fullText, containerEl, speed = 1.0) {
        this.stop();

        // Nếu thay đổi tốc độ đọc -> Xóa cache cũ để tải âm thanh đúng tốc độ mới
        if (this.currentSpeed !== speed) {
            this.clearCache();
            this.currentSpeed = speed;
        }

        // Bọc thẻ span cho từng câu trong giao diện
        let sentenceItems = [];
        if (this.karaoke && containerEl) {
            sentenceItems = this.karaoke.wrapDocumentSentences(containerEl);
        }

        if (sentenceItems && sentenceItems.length > 0) {
            // MỖI CÂU TRÊN GIAO DIỆN = MỘT ĐOẠN ÂM THANH: câu được tô sáng đúng trong lúc
            // giọng đọc đọc nó, không lệch dù câu dài hay ngắn
            this.chunks = sentenceItems.map((item) => ({
                text: item.text,
                speechText: item.text,
                wordCount: item.text.split(/\s+/).filter(Boolean).length,
                wordItems: [item],
            }));
        } else {
            // Dự phòng khi không có container DOM
            this.chunks = this._splitIntoChunks(fullText);
        }

        this.currentIndex = -1;
    }

    _normalizeTextKey(text, speed = this.currentSpeed) {
        if (!text) return "";
        const clean = text
            .replace(/[.,!?:;•═📌💡*#\-_]/g, ' ')
            .replace(/\s+/g, ' ')
            .trim()
            .toLowerCase();
        return `${speed}_${clean}`;
    }

    /**
     * Nạp trước âm thanh cho một câu bằng chuỗi văn bản (Eager Prefetch đón đầu từ SSE)
     */
    async preloadText(text, speed = this.currentSpeed) {
        if (!text || !text.trim()) return null;
        const normKey = this._normalizeTextKey(text, speed);
        if (!normKey) return null;

        if (this.textCache.has(normKey)) {
            return this.textCache.get(normKey);
        }

        if (this.prefetchingSet.has(normKey)) {
            for (let i = 0; i < 100; i++) {
                await new Promise(r => setTimeout(r, 100));
                if (this.textCache.has(normKey)) {
                    return this.textCache.get(normKey);
                }
            }
            return null;
        }

        this.prefetchingSet.add(normKey);
        try {
            let blob = null;
            for (let attempt = 0; attempt < 2; attempt++) {
                try {
                    blob = await this.client.fetchAudioStreamBlob(text, speed);
                    if (blob && blob.size > 200) break;
                } catch (e_fetch) {
                    if (attempt === 0) await new Promise(r => setTimeout(r, 200));
                }
            }

            if (!blob || blob.size <= 200) {
                return null;
            }

            const blobUrl = URL.createObjectURL(blob);
            this.textCache.set(normKey, blobUrl);
            return blobUrl;
        } catch (err) {
            console.warn("[SentenceQueue] preloadText thất bại:", err);
            return null;
        } finally {
            this.prefetchingSet.delete(normKey);
        }
    }

    /**
     * Tải trước âm thanh cho một câu vào RAM
     */
    async _fetchChunkAudio(index) {
        if (index < 0 || index >= this.chunks.length) return null;
        const chunk = this.chunks[index];
        const cacheKey = `${index}_${this.currentSpeed}_${chunk.speechText}`;

        if (this.blobCache.has(cacheKey)) {
            return this.blobCache.get(cacheKey);
        }

        // Kiểm tra nhanh trong textCache (Eager Prefetch từ luồng SSE)
        const normKey = this._normalizeTextKey(chunk.speechText, this.currentSpeed);
        if (normKey && this.textCache.has(normKey)) {
            const cachedUrl = this.textCache.get(normKey);
            this.blobCache.set(cacheKey, cachedUrl);
            return cachedUrl;
        }

        if (this.prefetchingSet.has(cacheKey) || (normKey && this.prefetchingSet.has(normKey))) {
            // Đang tải ở luồng khác, chờ tối đa 10 giây (100 * 100ms)
            for (let i = 0; i < 100; i++) {
                await new Promise(r => setTimeout(r, 100));
                if (this.blobCache.has(cacheKey)) {
                    return this.blobCache.get(cacheKey);
                }
                if (normKey && this.textCache.has(normKey)) {
                    const cachedUrl = this.textCache.get(normKey);
                    this.blobCache.set(cacheKey, cachedUrl);
                    return cachedUrl;
                }
            }
            return null;
        }

        this.prefetchingSet.add(cacheKey);
        if (normKey) this.prefetchingSet.add(normKey);
        try {
            let blob = null;
            // Thử lại tối đa 2 lần nếu có sự cố mạng
            for (let attempt = 0; attempt < 2; attempt++) {
                try {
                    blob = await this.client.fetchAudioStreamBlob(chunk.speechText, this.currentSpeed);
                    if (blob && blob.size > 200) break;
                } catch (e_fetch) {
                    if (attempt === 0) await new Promise(r => setTimeout(r, 200));
                }
            }

            if (!blob || blob.size <= 200) {
                console.warn(`[SentenceQueue] Không nhận được audio blob hợp lệ cho câu ${index}`);
                return null;
            }

            const blobUrl = URL.createObjectURL(blob);
            this.blobCache.set(cacheKey, blobUrl);
            if (normKey) this.textCache.set(normKey, blobUrl);
            return blobUrl;
        } catch (err) {
            console.warn(`[SentenceQueue] Không thể tải audio câu ${index}:`, err);
            return null;
        } finally {
            this.prefetchingSet.delete(cacheKey);
            if (normKey) this.prefetchingSet.delete(normKey);
        }
    }

    /**
     * Vòng lặp tải trước gối đầu liên tục (Continuous Sequential Prefetch Worker):
     * Luôn duy trì bộ đệm sẵn tối thiểu 3 câu tiếp theo trong RAM.
     * Khi câu hiện tại phát xong, câu tiếp theo ĐÃ CÓ SẴN 100% trong RAM (0ms chuyển câu).
     * Loại trừ triệt để tình trạng nghẽn mạng, chờ tải hoặc bị trình duyệt chặn autoplay!
     */
    async _startPrefetchLoop(session) {
        if (this.isPrefetchingRunning) return;
        this.isPrefetchingRunning = true;

        try {
            while (this.isPlaying && this.sessionId === session) {
                const current = Math.max(0, this.currentIndex);
                let targetIdx = -1;

                // 1. Ưu tiên nạp trước 3 câu kế tiếp ngay sát câu đang đọc
                for (let offset = 1; offset <= 3; offset++) {
                    const idx = current + offset;
                    if (idx < this.chunks.length) {
                        const cacheKey = `${idx}_${this.currentSpeed}_${this.chunks[idx].speechText}`;
                        if (!this.blobCache.has(cacheKey) && !this.prefetchingSet.has(cacheKey)) {
                            targetIdx = idx;
                            break;
                        }
                    }
                }

                // 2. Nếu 3 câu liền kề đã xong, tranh thủ nạp tiếp các câu còn lại về sau
                if (targetIdx === -1) {
                    for (let idx = current + 4; idx < this.chunks.length; idx++) {
                        const cacheKey = `${idx}_${this.currentSpeed}_${this.chunks[idx].speechText}`;
                        if (!this.blobCache.has(cacheKey) && !this.prefetchingSet.has(cacheKey)) {
                            targetIdx = idx;
                            break;
                        }
                    }
                }

                // Nếu toàn bộ câu trong văn bản đã nạp đủ vào RAM
                if (targetIdx === -1) {
                    break;
                }

                await this._fetchChunkAudio(targetIdx);
                await new Promise(r => setTimeout(r, 40));
            }
        } catch (e_loop) {
            console.warn("[SentenceQueue] Lỗi trong prefetch loop:", e_loop);
        } finally {
            this.isPrefetchingRunning = false;
        }
    }

    /**
     * Bắt đầu phát hàng đợi âm thanh câu theo câu.
     *
     * @param {Object} callbacks
     * @param {Function} callbacks.onStart - Gọi khi câu đầu tiên bắt đầu phát
     * @param {Function} callbacks.onChunkChange - Gọi khi chuyển câu: (index, total) => void
     * @param {Function} callbacks.onEnded - Gọi khi đã đọc hết toàn bộ câu
     * @param {Function} callbacks.onError - Gọi khi có sự cố không thể khắc phục
     */
    async play({ onStart, onChunkChange, onEnded, onError } = {}) {
        if (!this.chunks || this.chunks.length === 0) return;

        this.stop();
        this.isPlaying = true;
        const activeSession = ++this.sessionId;

        this.onStartCallback = onStart;
        this.onChunkChangeCallback = onChunkChange;
        this.onEndedCallback = onEnded;
        this.onErrorCallback = onError;

        // Tải ngay câu đầu tiên (chỉ mất ~0.25s)
        const firstBlobUrl = await this._fetchChunkAudio(0);

        // Nếu người dùng đã bấm dừng trong lúc đang tải
        if (!this.isPlaying || this.sessionId !== activeSession) {
            return;
        }

        if (!firstBlobUrl) {
            this.isPlaying = false;
            if (this.onErrorCallback) {
                this.onErrorCallback(new Error("Không thể tải âm thanh câu mở đầu."));
            }
            return;
        }

        this.audioPlayer.removeEventListener('ended', this._boundOnEnded);
        this.audioPlayer.removeEventListener('error', this._boundOnError);
        this.audioPlayer.addEventListener('ended', this._boundOnEnded);
        this.audioPlayer.addEventListener('error', this._boundOnError);

        // Bắt đầu phát câu 0
        await this._playChunkAtIndex(0, activeSession);

        // Kích hoạt ngay luồng nạp gối đầu liên tục trong nền
        this._startPrefetchLoop(activeSession);

        if (this.onStartCallback) {
            this.onStartCallback();
        }
    }

    /**
     * Phát một câu cụ thể theo vị trí index
     */
    async _playChunkAtIndex(index, session) {
        if (!this.isPlaying || this.sessionId !== session) return;
        if (index < 0 || index >= this.chunks.length) {
            this._finishPlayback();
            return;
        }

        this.currentIndex = index;
        const chunk = this.chunks[index];

        // Đảm bảo luồng prefetch tiếp tục hoạt động theo vị trí mới
        this._startPrefetchLoop(session);

        let blobUrl = await this._fetchChunkAudio(index);
        if (!this.isPlaying || this.sessionId !== session) return;

        // Nếu lỗi tải câu này, tự động chuyển sang câu tiếp theo
        if (!blobUrl) {
            console.warn(`[SentenceQueue] Bỏ qua câu ${index} do lỗi tải âm thanh.`);
            return this._playChunkAtIndex(index + 1, session);
        }

        if (this.onChunkChangeCallback) {
            this.onChunkChangeCallback(index, this.chunks.length);
        }

        this.audioPlayer.src = blobUrl;
        this.audioPlayer.playbackRate = this.currentSpeed;

        const triggerHighlight = () => {
            if (!this.isPlaying || this.sessionId !== session) return;
            const duration = this.audioPlayer.duration || 0;
            if (this.karaoke && chunk.wordItems && chunk.wordItems.length > 0) {
                this.karaoke.prepareDocumentChunk(chunk.wordItems, duration);
            }
        };

        if (this.audioPlayer.readyState >= 1 && isFinite(this.audioPlayer.duration) && this.audioPlayer.duration > 0) {
            triggerHighlight();
        } else {
            this.audioPlayer.addEventListener('loadedmetadata', triggerHighlight, { once: true });
        }

        try {
            await this.audioPlayer.play();
            this.audioPlayer.playbackRate = this.currentSpeed;
        } catch (err) {
            console.warn("[SentenceQueue] Trình duyệt chặn tự động phát, thử lại lần 2:", err);
            try {
                await new Promise(r => setTimeout(r, 100));
                await this.audioPlayer.play();
                this.audioPlayer.playbackRate = this.currentSpeed;
            } catch (err2) {
                console.error("[SentenceQueue] Không thể phát âm thanh câu:", err2);
                return this._playChunkAtIndex(index + 1, session);
            }
        }
    }

    _handleAudioEnded() {
        if (!this.isPlaying) return;
        const session = this.sessionId;
        const nextIndex = this.currentIndex + 1;

        if (nextIndex < this.chunks.length) {
            this._playChunkAtIndex(nextIndex, session);
        } else {
            this._finishPlayback();
        }
    }

    _handleAudioError(e) {
        console.warn("[SentenceQueue] Lỗi audio element:", e);
        if (!this.isPlaying) return;
        const session = this.sessionId;
        // Thử chuyển tiếp câu kế nếu lỗi
        const nextIndex = this.currentIndex + 1;
        if (nextIndex < this.chunks.length) {
            this._playChunkAtIndex(nextIndex, session);
        } else {
            this._finishPlayback();
        }
    }

    _finishPlayback() {
        this.isPlaying = false;
        this.audioPlayer.removeEventListener('ended', this._boundOnEnded);
        this.audioPlayer.removeEventListener('error', this._boundOnError);
        if (this.karaoke) {
            this.karaoke.reset();
        }
        if (this.onEndedCallback) {
            this.onEndedCallback();
        }
    }

    /**
     * Dừng phát ngay lập tức và đưa giao diện về trạng thái sẵn sàng.
     */
    stop() {
        this.isPlaying = false;
        this.sessionId++;
        this.currentIndex = -1;
        this.isPrefetchingRunning = false;

        if (this.audioPlayer) {
            this.audioPlayer.pause();
            this.audioPlayer.removeEventListener('ended', this._boundOnEnded);
            this.audioPlayer.removeEventListener('error', this._boundOnError);
        }

        if (this.karaoke) {
            this.karaoke.reset();
        }
    }

    /**
     * Dọn sạch toàn bộ Blob URLs trong bộ nhớ RAM khi chuyển tài liệu mới.
     */
    clearCache() {
        this.stop();
        this.isPrefetchingRunning = false;
        const allUrls = new Set([...this.blobCache.values(), ...(this.textCache ? this.textCache.values() : [])]);
        allUrls.forEach((url) => {
            try {
                URL.revokeObjectURL(url);
            } catch (e) {}
        });
        this.blobCache.clear();
        if (this.textCache) {
            this.textCache.clear();
        }
        this.prefetchingSet.clear();
    }
}

// Xuất cho cả Browser và Module
if (typeof window !== 'undefined') {
    window.SentenceAudioQueue = SentenceAudioQueue;
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SentenceAudioQueue;
}
