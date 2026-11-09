/**
 * MEDIDOCX AI - LOGIC ĐIỀU KHIỂN GIAO DIỆN WEB COMPANION (v3.3)
 * Tối ưu đa thiết bị: Mobile & Laptop
 * Hỗ trợ chế độ Sáng / Tối (Dark / Light)
 * Phóng to cỡ chữ thực sự (120% / 140%) qua Root Rem Scaling
 * Nút chụp tiếp 1 chạm ngay đầu kết quả
 */

document.addEventListener('DOMContentLoaded', async () => {
    const client = new A11yMobileClient();

    // 1. CÁC MÀN HÌNH TRẠNG THÁI CHÍNH
    const actionScreen = document.getElementById('action-screen');
    const loadingCard = document.getElementById('loading-card');
    const resultCard = document.getElementById('result-card');

    // Nút chụp tiếp trực tiếp & quay lại màn hình chính
    const btnChupTiepTop = document.getElementById('btnChupTiepTop');
    const btnChupTiepBottom = document.getElementById('btnChupTiepBottom');
    const btnVeTrangChu = document.getElementById('btnVeTrangChu');

    // 2. CHUYỂN CHẾ ĐỘ THUỐC / VĂN BẢN
    const modeSelector = document.getElementById('mode-selector');
    const headerSubtitle = document.getElementById('header-subtitle');
    const btnChonThuoc = document.getElementById('btnChonThuoc');
    const btnChonVanBan = document.getElementById('btnChonVanBan');
    const sectionThuoc = document.getElementById('section-thuoc');
    const sectionVanban = document.getElementById('section-vanban');

    // 3. NÚT CHỤP ẢNH CHÍNH
    const btnChupThuoc = document.getElementById('btnChupThuoc');
    const iconChupThuoc = document.getElementById('iconChupThuoc');
    const titleChupThuoc = document.getElementById('titleChupThuoc');
    const subChupThuoc = document.getElementById('subChupThuoc');

    const btnChupVanBan = document.getElementById('btnChupVanBan');
    const iconChupVanBan = document.getElementById('iconChupVanBan');
    const titleChupVanBan = document.getElementById('titleChupVanBan');
    const subChupVanBan = document.getElementById('subChupVanBan');

    const cameraInput = document.getElementById('camera-input');
    const fileInput = document.getElementById('file-input');
    const dropZoneThuoc = document.getElementById('drop-zone-thuoc');
    const dropZoneVanban = document.getElementById('drop-zone-vanban');

    // 4. TÌM THUỐC NHANH
    const medSearchInput = document.getElementById('med-search-input');
    const btnSearchMed = document.getElementById('btn-search-med');
    const quickChips = document.querySelectorAll('.med-chip');

    // 5. TRƯỜNG HIỂN THỊ KẾT QUẢ
    const resultBadge = document.getElementById('result-badge');
    const noticeNotMedicine = document.getElementById('notice-not-medicine');
    const btnQuickSwitchDoc = document.getElementById('btn-quick-switch-doc');

    const medicineDisplayBox = document.getElementById('medicine-display-box');
    const medDetailsContainer = document.getElementById('med-details-container');
    const docDisplayBox = document.getElementById('doc-display-box');

    const lblTenThuoc = document.getElementById('lblTenThuoc');
    const lblThoiDiem = document.getElementById('lblThoiDiem');
    const lblLieuNguoiLon = document.getElementById('lblLieuNguoiLon');
    const lblLieuTreEm = document.getElementById('lblLieuTreEm');
    const lblCongDung = document.getElementById('lblCongDung');
    const lblLuuYChiTiet = document.getElementById('lblLuuYChiTiet');
    const lblHoatChat = document.getElementById('lblHoatChat');
    const btnPhanTichAI = document.getElementById('btnPhanTichAI');

    const aiExtraContainer = document.getElementById('ai-extra-container');
    const boxHanDungAI = document.getElementById('box-han-dung-ai');
    const lblHanDungAI = document.getElementById('lblHanDungAI');
    const boxThongTinMoAI = document.getElementById('box-thong-tin-mo-ai');
    const lblThongTinMoAI = document.getElementById('lblThongTinMoAI');

    const lblTieuDeVanBan = document.getElementById('lblTieuDeVanBan');
    const lblDocModeLabel = document.getElementById('lblDocModeLabel');
    const lblDocContent = document.getElementById('lblDocContent');
    const btnDocToggleSummary = document.getElementById('btnDocToggleSummary');
    const iconDocToggle = document.getElementById('iconDocToggle');
    const textDocToggle = document.getElementById('textDocToggle');
    const rawOcrText = document.getElementById('raw-ocr-text');



    // 6. ĐIỀU KHIỂN ÂM THANH
    const btnNgheLai = document.getElementById('btnNgheLai');
    const iconNgheLai = document.getElementById('icon-nghe-lai');
    const textNgheLai = document.getElementById('text-nghe-lai');
    const btnLuuYThuoc = document.getElementById('btnLuuYThuoc');
    const iconLuuY = document.getElementById('icon-luu-y');
    const textLuuY = document.getElementById('text-luu-y');
    const btnDungDoc = document.getElementById('btnDungDoc');
    const iconDungDoc = document.getElementById('icon-dung-doc');
    const textDungDoc = document.getElementById('text-dung-doc');
    const audioSecondaryRow = document.querySelector('.audio-secondary-row');
    const speedPills = document.querySelectorAll('.btn-speed-pill');
    const audioPlayer = document.getElementById('audio-player');

    // 7. CÀI ĐẶT TRỢ NĂNG, THEME & GIỌNG ĐỌC
    const btnThemeToggle = document.getElementById('btn-theme-toggle');
    const btnInfoToggle = document.getElementById('btn-info-toggle');
    const infoModal = document.getElementById('info-modal');
    const btnCloseInfo = document.getElementById('btn-close-info');
    const btnCloseInfoFooter = document.getElementById('btn-close-info-footer');

    const btnFontNormal = document.getElementById('btn-font-normal');
    const btnFontLarge = document.getElementById('btn-font-large');
    const btnFontXLarge = document.getElementById('btn-font-xlarge');
    const btnFontLexend = document.getElementById('btn-font-lexend');
    const btnFontDyslexic = document.getElementById('btn-font-dyslexic');

    // Biến trạng thái
    let currentMode = 'thuoc'; // 'thuoc' | 'vanban'
    let currentToken = null;
    let currentAudioUrl = null;
    let currentWarningAudioUrl = null;
    let currentSpeed = 1.0;

    // ==========================================================
    // TRẠNG THÁI CHAT (tách biệt hoàn toàn với logic nhận diện)
    // ==========================================================
    const chatState = {
        isOpen: false,
        isStreaming: false,
        history: [],          // [{role, content}, ...] — lịch sử hội thoại
        context: {},          // Thông tin thuốc hiện tại
        abortController: null // AbortController để huỷ stream đang chạy
    };

    // ==========================================================
    // QUẢN LÝ TIẾN TRÌNH ÂM THANH CHẾ ĐỘ VĂN BẢN (TOÀN VĂN & TÓM TẮT ĐỘC LẬP)
    // ==========================================================
    let docState = {
        // Raw (Toàn văn gốc 100%)
        rawText: '',
        rawBlobUrl: null,       // URL.createObjectURL(blob) trong RAM điện thoại
        rawSpeed: null,         // Tốc độ đã tạo
        rawLoading: false,      // Đang stream từ server về RAM

        // Summary (Bản tóm tắt ý chính)
        summaryText: '',
        summarySpeechText: '',  // Văn bản sạch để đọc không dính ký tự bullet
        summaryBlobUrl: null,   // URL.createObjectURL(blob) trong RAM điện thoại
        summarySpeed: null,     // Tốc độ đã tạo
        summaryLoading: false,  // Đang stream từ server về RAM
        hasSummarized: false,

        // Tab hiển thị hiện tại (false: Toàn văn, true: Tóm tắt)
        isSummaryView: false
    };

    function revokeDocBlobs() {
        if (docState.rawBlobUrl) {
            try { URL.revokeObjectURL(docState.rawBlobUrl); } catch (e) {}
            docState.rawBlobUrl = null;
            docState.rawSpeed = null;
        }
        if (docState.summaryBlobUrl) {
            try { URL.revokeObjectURL(docState.summaryBlobUrl); } catch (e) {}
            docState.summaryBlobUrl = null;
            docState.summarySpeed = null;
        }
        docState.rawLoading = false;
        docState.summaryLoading = false;
    }

    function updateDocAudioButtonUI() {
        if (currentMode !== 'vanban') return;

        const isPlaying = !audioPlayer.paused && audioPlayer.currentTime > 0;

        if (isPlaying) {
            if (iconNgheLai) iconNgheLai.innerText = "⏹";
            if (textNgheLai) textNgheLai.innerText = "DỪNG ĐỌC";
            return;
        }

        if (docState.isSummaryView) {
            // TAB TÓM TẮT Ý CHÍNH
            if (docState.summaryLoading) {
                if (iconNgheLai) iconNgheLai.innerText = "⏳";
                if (textNgheLai) textNgheLai.innerText = "ĐANG TẢI GIỌNG TÓM TẮT...";
            } else if (docState.summaryBlobUrl) {
                if (iconNgheLai) iconNgheLai.innerText = "🔊";
                if (textNgheLai) textNgheLai.innerText = "BẤM ĐỂ NGHE LẠI";
            } else {
                if (iconNgheLai) iconNgheLai.innerText = "🔊";
                if (textNgheLai) textNgheLai.innerText = "NGHE ĐỌC TÓM TẮT";
            }
        } else {
            // TAB TOÀN VĂN GỐC (100%)
            if (docState.rawLoading) {
                if (iconNgheLai) iconNgheLai.innerText = "⏳";
                if (textNgheLai) textNgheLai.innerText = "ĐANG TẢI GIỌNG TOÀN VĂN...";
            } else if (docState.rawBlobUrl) {
                if (iconNgheLai) iconNgheLai.innerText = "🔊";
                if (textNgheLai) textNgheLai.innerText = "BẤM ĐỂ NGHE LẠI";
            } else {
                if (iconNgheLai) iconNgheLai.innerText = "🔊";
                if (textNgheLai) textNgheLai.innerText = "NGHE TOÀN VĂN GỐC";
            }
        }
    }

    // ==========================================================
    // KHỞI TẠO CÁC CÀI ĐẶT TỪ LOCALSTORAGE
    // ==========================================================
    // 1. Chế độ Sáng / Tối
    const savedTheme = localStorage.getItem('medidocx_theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        btnThemeToggle.innerText = '🌙';
    } else {
        document.body.classList.remove('light-theme');
        btnThemeToggle.innerText = '☀️';
    }

    btnThemeToggle.addEventListener('click', () => {
        const isLight = document.body.classList.toggle('light-theme');
        btnThemeToggle.innerText = isLight ? '🌙' : '☀️';
        localStorage.setItem('medidocx_theme', isLight ? 'light' : 'dark');
    });

    // 2. Cỡ chữ (Root Rem Scaling)
    function applyFontSize(size) {
        document.documentElement.classList.remove('font-large', 'font-xlarge');
        document.body.classList.remove('font-large', 'font-xlarge');
        btnFontNormal.classList.remove('active');
        btnFontLarge.classList.remove('active');
        btnFontXLarge.classList.remove('active');

        if (size === 'large') {
            document.documentElement.classList.add('font-large');
            document.body.classList.add('font-large');
            btnFontLarge.classList.add('active');
        } else if (size === 'xlarge') {
            document.documentElement.classList.add('font-xlarge');
            document.body.classList.add('font-xlarge');
            btnFontXLarge.classList.add('active');
        } else {
            btnFontNormal.classList.add('active');
        }
        localStorage.setItem('medidocx_fontsize', size);
    }

    const savedFontSize = localStorage.getItem('medidocx_fontsize') || 'normal';
    applyFontSize(savedFontSize);

    btnFontNormal.addEventListener('click', () => applyFontSize('normal'));
    btnFontLarge.addEventListener('click', () => applyFontSize('large'));
    btnFontXLarge.addEventListener('click', () => applyFontSize('xlarge'));

    // 3. Phông chữ trợ năng
    function applyFontFamily(font) {
        document.body.classList.remove('font-opendyslexic', 'font-lexend');
        btnFontLexend.classList.remove('active');
        btnFontDyslexic.classList.remove('active');

        if (font === 'dyslexic') {
            document.body.classList.add('font-opendyslexic');
            btnFontDyslexic.classList.add('active');
        } else {
            document.body.classList.add('font-lexend');
            btnFontLexend.classList.add('active');
        }
        localStorage.setItem('medidocx_fontfamily', font);
    }

    const savedFontFamily = localStorage.getItem('medidocx_fontfamily') || 'lexend';
    applyFontFamily(savedFontFamily);

    btnFontLexend.addEventListener('click', () => applyFontFamily('lexend'));
    btnFontDyslexic.addEventListener('click', () => applyFontFamily('dyslexic'));

    // Nhận diện loại thiết bị
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
                     (window.innerWidth <= 768 && ('ontouchstart' in window || navigator.maxTouchPoints > 0));

    if (!isMobile) {
        // Trên Laptop/PC: đổi nhãn nút chọn file
        if (titleChupThuoc) titleChupThuoc.innerText = "CHỌN ẢNH THUỐC TỪ MÁY";
        if (subChupThuoc) subChupThuoc.innerText = "Bấm để chọn file ảnh thuốc trên máy tính";
        if (iconChupThuoc) iconChupThuoc.innerText = "📁";

        if (titleChupVanBan) titleChupVanBan.innerText = "CHỌN TÀI LIỆU TỪ MÁY";
        if (subChupVanBan) subChupVanBan.innerText = "Bấm để chọn file tài liệu trên máy tính";
        if (iconChupVanBan) iconChupVanBan.innerText = "📁";
    }

    // ==========================================================
    // ĐIỀU PHỐI MÀN HÌNH (STATE-DRIVEN UI)
    // ==========================================================
    function setScreen(screen) {
        if (screen === 'action') {
            if (modeSelector) modeSelector.style.display = 'grid';
            actionScreen.style.display = 'flex';
            loadingCard.style.display = 'none';
            resultCard.style.display = 'none';
        } else if (screen === 'loading') {
            if (modeSelector) modeSelector.style.display = 'none';
            actionScreen.style.display = 'none';
            loadingCard.style.display = 'flex';
            resultCard.style.display = 'none';
        } else if (screen === 'result') {
            if (modeSelector) modeSelector.style.display = 'none';
            actionScreen.style.display = 'none';
            loadingCard.style.display = 'none';
            resultCard.style.display = 'flex';
        }
    }

    // Mặc định vào màn hình Sẵn sàng
    setScreen('action');

    // Nút chụp tiếp ở cuối trang kết quả
    if (btnChupTiepBottom) {
        btnChupTiepBottom.addEventListener('click', () => {
            stopAllAudio();
        });
    }

    // Nút quay lại màn hình chính tìm kiếm
    if (btnVeTrangChu) {
        btnVeTrangChu.addEventListener('click', () => {
            revokeDocBlobs();
            stopAllAudio();
            setScreen('action');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }

    // ==========================================================
    // CHUYỂN TAB CHẾ ĐỘ (TỐI GIẢN TOÀN DIỆN CHO MỖI CHẾ ĐỘ)
    // ==========================================================
    function setMode(mode) {
        revokeDocBlobs();
        currentMode = mode;
        stopAllAudio();
        noticeNotMedicine.style.display = 'none';

        if (mode === 'thuoc') {
            if (headerSubtitle) headerSubtitle.innerText = "Trợ lý nhận diện và hướng dẫn dùng thuốc an toàn";
            btnChonThuoc.classList.add('active');
            btnChonVanBan.classList.remove('active');
            sectionThuoc.style.display = 'block';
            sectionVanban.style.display = 'none';
            medicineDisplayBox.style.display = 'flex';
            docDisplayBox.style.display = 'none';
            if (iconNgheLai) iconNgheLai.innerText = "🔊";
            if (textNgheLai) textNgheLai.innerText = "BẤM ĐỂ NGHE LẠI";
            btnLuuYThuoc.style.display = 'flex';
            if (audioSecondaryRow) audioSecondaryRow.classList.remove('single-btn');
            if (btnChupTiepTop) btnChupTiepTop.innerText = "📸 BẤM ĐỂ CHỤP TIẾP THUỐC MỚI";
            if (btnChupTiepBottom) btnChupTiepBottom.innerText = "📸 BẤM ĐỂ CHỤP TIẾP THUỐC MỚI";
            if (btnVeTrangChu) btnVeTrangChu.innerHTML = '<span class="back-arrow-icon">⬅</span> <span>QUAY LẠI TRANG CHÍNH</span>';
        } else {
            if (headerSubtitle) headerSubtitle.innerText = "Trợ lý đọc và tóm tắt văn bản to rõ";
            btnChonVanBan.classList.add('active');
            btnChonThuoc.classList.remove('active');
            sectionVanban.style.display = 'block';
            sectionThuoc.style.display = 'none';
            docDisplayBox.style.display = 'flex';
            medicineDisplayBox.style.display = 'none';
            updateDocAudioButtonUI();
            btnLuuYThuoc.style.display = 'none';
            if (audioSecondaryRow) audioSecondaryRow.classList.add('single-btn');
            if (btnChupTiepTop) btnChupTiepTop.innerText = "📸 BẤM ĐỂ CHỤP TIẾP VĂN BẢN MỚI";
            if (btnChupTiepBottom) btnChupTiepBottom.innerText = "📸 BẤM ĐỂ CHỤP TIẾP VĂN BẢN MỚI";
            if (btnVeTrangChu) btnVeTrangChu.innerHTML = '<span class="back-arrow-icon">⬅</span> <span>QUAY LẠI TRANG CHÍNH</span>';
        }
    }

    btnChonThuoc.addEventListener('click', () => setMode('thuoc'));
    btnChonVanBan.addEventListener('click', () => setMode('vanban'));
    if (btnQuickSwitchDoc) {
        btnQuickSwitchDoc.addEventListener('click', () => {
            setMode('vanban');
            setScreen('action');
        });
    }

    // ==========================================================
    // SỰ KIỆN NÚT CHỤP CHÍNH & CHỌN FILE
    // ==========================================================
    const linkFileThuoc = document.getElementById('link-file-thuoc');
    const linkFileVanban = document.getElementById('link-file-vanban');

    if (btnChupThuoc) {
        btnChupThuoc.addEventListener('click', () => {
            stopAllAudio();
            currentMode = 'thuoc';
        });
    }

    if (btnChupVanBan) {
        btnChupVanBan.addEventListener('click', () => {
            stopAllAudio();
            currentMode = 'vanban';
        });
    }

    if (linkFileThuoc) {
        linkFileThuoc.addEventListener('click', () => {
            stopAllAudio();
            currentMode = 'thuoc';
        });
    }

    if (linkFileVanban) {
        linkFileVanban.addEventListener('click', () => {
            stopAllAudio();
            currentMode = 'vanban';
        });
    }

    cameraInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleImageFile(e.target.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleImageFile(e.target.files[0]);
        }
    });

    // Kéo thả & Ctrl + V trên máy tính
    [dropZoneThuoc, dropZoneVanban].forEach(zone => {
        if (!zone) return;
        zone.addEventListener('dragover', (e) => e.preventDefault());
        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                handleImageFile(e.dataTransfer.files[0]);
            }
        });
        zone.addEventListener('click', () => fileInput.click());
    });

    window.addEventListener('paste', (e) => {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (let item of items) {
            if (item.type.indexOf('image') !== -1) {
                const blob = item.getAsFile();
                handleImageFile(blob);
                break;
            }
        }
    });

    // ==========================================================
    // NÉN ẢNH NHẸ TRÊN CLIENT (CHỐNG NGHẼN MẠNG NGROK)
    // ==========================================================
    async function compressImageForOCR(file, maxSide = 1600) {
        if (!file || !file.type || !file.type.startsWith('image/')) return file;
        return new Promise((resolve) => {
            const img = new Image();
            const url = URL.createObjectURL(file);
            img.onload = () => {
                URL.revokeObjectURL(url);
                let w = img.width;
                let h = img.height;
                if (Math.max(w, h) > maxSide) {
                    const scale = maxSide / Math.max(w, h);
                    w = Math.round(w * scale);
                    h = Math.round(h * scale);
                }
                const canvas = document.createElement('canvas');
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext('2d');
                ctx.imageSmoothingEnabled = true;
                ctx.imageSmoothingQuality = 'high';
                ctx.drawImage(img, 0, 0, w, h);
                canvas.toBlob((blob) => {
                    resolve(blob || file);
                }, 'image/jpeg', 0.85);
            };
            img.onerror = () => {
                URL.revokeObjectURL(url);
                resolve(file);
            };
            img.src = url;
        });
    }

    // ==========================================================
    // XỬ LÝ ẢNH CHÍNH
    // ==========================================================
    async function handleImageFile(file) {
        if (!file) return;

        revokeDocBlobs();
        stopAllAudio();
        setScreen('loading');
        noticeNotMedicine.style.display = 'none';

        const loadingTitle = document.getElementById('loading-title');
        const loadingSub = document.getElementById('loading-sub');

        try {
            const optimizedBlob = await compressImageForOCR(file, 1600);

            if (currentMode === 'thuoc') {
                loadingTitle.innerText = "AI đang đọc tên thuốc và cách dùng...";
                loadingSub.innerText = "Ưu tiên đối chiếu dữ liệu y tế chuẩn";

                const data = await client.recognizeMedicineAppInventor(optimizedBlob, currentSpeed);
                renderMedicineStep1(data);
            } else {
                loadingTitle.innerText = "Đang trích xuất 100% văn bản gốc...";
                loadingSub.innerText = "Giữ nguyên vẹn câu chữ bằng phông OpenDyslexic cho bạn";

                const data = await client.processDocumentAppInventor(optimizedBlob, currentSpeed);
                renderDocumentResult(data);
            }
        } catch (err) {
            alert(`Lỗi xử lý hình ảnh: ${err.message}`);
            setScreen('action');
        } finally {
            cameraInput.value = '';
            fileInput.value = '';
        }
    }

    // ==========================================================
    // HIỂN THỊ KẾT QUẢ THUỐC (BƯỚC 1)
    // ==========================================================
    function renderMedicineStep1(data) {
        currentToken = data.image_token || null;
        currentAudioUrl = data.audio_url || null;
        currentWarningAudioUrl = data.warning_audio_url || null;

        btnLuuYThuoc.disabled = true;
        btnLuuYThuoc.classList.remove('active-glow');
        if (iconLuuY) iconLuuY.innerText = "🔔";
        if (textLuuY) textLuuY.innerText = "Nghe lưu ý";

        setScreen('result');
        medicineDisplayBox.style.display = 'flex';
        docDisplayBox.style.display = 'none';
        resultBadge.style.display = 'block';
        if (rawOcrText) rawOcrText.innerText = data.raw_ocr_text || data.raw_text || "(Không có văn bản quét)";
        if (btnChupTiepBottom) btnChupTiepBottom.innerText = "📸 BẤM ĐỂ CHỤP TIẾP THUỐC MỚI";
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // TÌNH HUỐNG 0: ẢNH CHỤP QUÁ MỜ / RUNG TAY
        if (data.is_unreadable || data.status === 'unreadable_image') {
            noticeNotMedicine.style.display = 'none';
            if (medDetailsContainer) medDetailsContainer.style.display = 'none';
            resultBadge.style.display = '';
            resultBadge.className = "badge badge-not-db";
            resultBadge.innerText = "📸 ẢNH BỊ MỜ - VUI LÒNG CHỤP LẠI";
            if (medicineDisplayBox) medicineDisplayBox.style.display = 'flex';
            if (btnLuuYThuoc) btnLuuYThuoc.style.display = 'none';

            lblTenThuoc.innerText = "Ảnh chụp thuốc bị mờ";
            btnPhanTichAI.style.display = 'none';

            if (currentAudioUrl) playAudio(currentAudioUrl);
            return;
        }

        // TÌNH HUỐNG 1: ẢNH LÀ VĂN BẢN (KHÔNG PHẢI THUỐC)
        if (data.is_medicine === false && !data.is_toxic) {
            noticeNotMedicine.style.display = 'flex';
            if (medDetailsContainer) medDetailsContainer.style.display = 'none';
            resultBadge.style.display = 'none';
            if (medicineDisplayBox) medicineDisplayBox.style.display = 'none';
            btnPhanTichAI.style.display = 'none';
            if (btnLuuYThuoc) btnLuuYThuoc.style.display = 'none';

            if (currentAudioUrl) {
                playAudio(currentAudioUrl, () => {
                    if (iconNgheLai) iconNgheLai.innerText = "🔊";
                    if (textNgheLai) textNgheLai.innerText = "BẤM ĐỂ NGHE LẠI";
                });
            }
            return;
        }

        // TÌNH HUỐNG 2: ĐÃ CÓ TRONG CSDL CHUẨN (ĐÃ KIỂM ĐỊNH)
        if (data.found_in_db) {
            noticeNotMedicine.style.display = 'none';
            resultBadge.style.display = '';
            if (medicineDisplayBox) medicineDisplayBox.style.display = 'flex';
            if (btnLuuYThuoc) btnLuuYThuoc.style.display = 'flex';
            if (medDetailsContainer) medDetailsContainer.style.display = ''; // Hiện các ô chi tiết khi có dữ liệu
            resultBadge.className = "badge badge-db";
            resultBadge.innerText = "✅ THÔNG TIN ĐÃ KIỂM ĐỊNH Y TẾ CHÍNH XÁC";

            lblTenThuoc.innerText = data.name || "Thuốc trong CSDL";
            lblCongDung.innerText = data.indication || "Theo chỉ định bác sĩ";
            lblHoatChat.innerText = `Hoạt chất: ${data.active_ingredient || "Theo bao bì"}`;
            lblThoiDiem.innerText = data.meal_timing || "Uống theo chỉ định";
            lblLieuNguoiLon.innerText = data.dosage_adult || "Chưa có thông tin";
            lblLieuTreEm.innerText = data.dosage_child || "Chưa có thông tin";
            lblLuuYChiTiet.innerText = data.warning || "Không có lưu ý đặc biệt";

            if (aiExtraContainer) aiExtraContainer.style.display = 'none';
            btnPhanTichAI.style.display = 'none';

            if (currentAudioUrl) {
                playAudio(currentAudioUrl, () => {
                    if (iconNgheLai) iconNgheLai.innerText = "🔊";
                    if (textNgheLai) textNgheLai.innerText = "ĐANG ĐỌC HƯỚNG DẪN...";
                });
            }
            return;
        }

        // TÌNH HUỐNG 3: CHƯA CÓ TRONG CSDL -> ẨN CÁC Ô CHI TIẾT TRỐNG RỖNG & ĐỔI NỘI DUNG KHUNG CAM
        noticeNotMedicine.style.display = 'none';
        resultBadge.style.display = '';
        if (medicineDisplayBox) medicineDisplayBox.style.display = 'flex';
        if (btnLuuYThuoc) btnLuuYThuoc.style.display = 'none';
        if (medDetailsContainer) medDetailsContainer.style.display = 'none'; // Ẩn các ô thời điểm, liều lượng, công dụng
        resultBadge.className = "badge badge-not-db";
        resultBadge.innerText = "Không có dữ liệu thuốc này, vui lòng nhờ người thân hỗ trợ hoặc nhờ tư vấn của chuyên gia y tế, bác sĩ hoặc dược sĩ.";

        lblTenThuoc.innerText = data.name || "Chưa có trong cơ sở dữ liệu";

        btnPhanTichAI.style.display = 'block';
        btnPhanTichAI.disabled = false;
        btnPhanTichAI.innerText = "🤖 BẤM ĐỂ PHÂN TÍCH BẰNG AI 🤖";

        if (currentAudioUrl) {
            playAudio(currentAudioUrl, () => {
                if (iconNgheLai) iconNgheLai.innerText = "🔊";
                if (textNgheLai) textNgheLai.innerText = "ĐANG PHÁT THÔNG BÁO...";
            });
        }
    }

    // ==========================================================
    // BƯỚC 2: PHÂN TÍCH BẰNG AI
    // ==========================================================
    btnPhanTichAI.addEventListener('click', async () => {
        if (!currentToken || btnPhanTichAI.disabled) return;

        stopAllAudio();
        setScreen('loading');
        const loadingTitle = document.getElementById('loading-title');
        const loadingSub = document.getElementById('loading-sub');
        loadingTitle.innerText = "AI đang đọc chuyên sâu vỏ hộp thuốc...";
        loadingSub.innerText = "Đang tổng hợp thông tin và sinh giọng đọc";

        try {
            const aiData = await client.analyzeMedicineAI(currentToken, currentSpeed);
            renderMedicineStep2AI(aiData);
        } catch (err) {
            alert(`Lỗi phân tích AI: ${err.message}`);
            setScreen('result');
        }
    });

    function renderMedicineStep2AI(data) {
        const med = data.medicine || data;
        currentAudioUrl = data.audio_url || null;
        currentWarningAudioUrl = data.warning_audio_url || null;

        setScreen('result');
        btnPhanTichAI.style.display = 'none';
        if (medDetailsContainer) medDetailsContainer.style.display = ''; // Hiện lại các ô chi tiết khi AI đã có dữ liệu!

        if (data.is_toxic || data.safety_level === 'LETHAL_TOXIC') {
            resultBadge.className = "badge badge-danger";
            resultBadge.innerText = "☠️ NGUY HIỂM: HÓA CHẤT ĐỘC HẠI - CẤM UỐNG!";
        } else {
            resultBadge.className = "badge badge-ai";
            resultBadge.innerText = "🤖 THÔNG TIN TRA CỨU TỰ ĐỘNG BẰNG AI";
        }

        lblTenThuoc.innerText = med.name || "Thuốc nhận diện AI";
        lblCongDung.innerText = med.indication || "Điều trị theo hướng dẫn y tế";
        lblHoatChat.innerText = `Hoạt chất: ${med.active_ingredient || "Theo bao bì"}`;
        lblThoiDiem.innerText = med.meal_timing || "Uống theo hướng dẫn";
        lblLieuNguoiLon.innerText = med.dosage_adult || "Theo chỉ định bác sĩ";
        lblLieuTreEm.innerText = med.dosage_child || "Cần hỏi ý kiến bác sĩ";
        lblLuuYChiTiet.innerText = med.warning || "Tham khảo ý kiến bác sĩ trước khi dùng";

        const rawExpiry = (med.expiry_date || data.expiry_date || "").trim();
        const rawUnclear = (med.unclear_info || data.unclear_info || "").trim();

        // Ẩn hạn dùng hoàn toàn nếu không có hoặc là thông tin không rõ ràng để tránh lãng phí diện tích hiển thị
        const invalidExpList = ["chưa rõ", "không rõ", "không thấy", "xem trên bao bì", "chưa xác định", "không có", "n/a", "theo bao bì"];
        const hasValidExpiry = rawExpiry && !invalidExpList.some(k => rawExpiry.toLowerCase().includes(k));

        const invalidUnclearList = ["không phát hiện phần không rõ", "không rõ", "rõ ràng", "không có", "n/a", "không phát hiện"];
        const hasValidUnclear = rawUnclear && !invalidUnclearList.some(k => rawUnclear.toLowerCase().includes(k));

        if (aiExtraContainer) {
            let hasExtra = false;
            if (hasValidExpiry && boxHanDungAI && lblHanDungAI) {
                lblHanDungAI.innerText = rawExpiry;
                boxHanDungAI.style.display = 'block';
                hasExtra = true;
            } else if (boxHanDungAI) {
                boxHanDungAI.style.display = 'none';
            }

            if (hasValidUnclear && boxThongTinMoAI && lblThongTinMoAI) {
                lblThongTinMoAI.innerText = rawUnclear;
                boxThongTinMoAI.style.display = 'block';
                hasExtra = true;
            } else if (boxThongTinMoAI) {
                boxThongTinMoAI.style.display = 'none';
            }

            aiExtraContainer.style.display = hasExtra ? 'flex' : 'none';
        }

        if (rawOcrText) rawOcrText.innerText = data.raw_ocr_text || data.raw_text || "(Phân tích trực tiếp qua AI Vision)";

        if (currentAudioUrl) {
            playAudio(currentAudioUrl, () => {
                if (iconNgheLai) iconNgheLai.innerText = "🔊";
                if (textNgheLai) textNgheLai.innerText = "ĐANG ĐỌC KẾT QUẢ AI...";
            });
        }
    }

    // ==========================================================
    // HIỂN THỊ KẾT QUẢ VĂN BẢN (CHẾ ĐỘ ĐỌC NGUYÊN VĂN & TÓM TẮT DYSLEXIA)
    // ==========================================================
    function renderDocumentResult(data) {
        revokeDocBlobs();
        stopAllAudio();

        if (data.is_unreadable || data.status === 'unreadable_image') {
            docState.rawText = data.raw_text || "Ảnh chụp quá mờ hoặc bị nhòe chữ. Vui lòng chụp lại ảnh rõ nét hơn.";
            docState.summaryText = data.all_bullets || "• Ảnh chụp bị mờ, nhòe nét hoặc thiếu sáng.\n• Vui lòng giữ chắc tay và chụp lại ảnh rõ nét hơn.";
            docState.summarySpeechText = data.plain_speech_text || "Ảnh chụp bị mờ, nhòe nét hoặc thiếu ánh sáng. Vui lòng giữ chắc tay và chụp lại ảnh rõ nét hơn.";
            docState.hasSummarized = false;
            docState.isSummaryView = false;

            setScreen('result');
            medicineDisplayBox.style.display = 'none';
            docDisplayBox.style.display = 'flex';
            resultBadge.style.display = 'none';
            if (btnChupTiepBottom) btnChupTiepBottom.innerText = "📸 BẤM ĐỂ CHỤP VĂN BẢN MỚI";
            window.scrollTo({ top: 0, behavior: 'smooth' });

            if (lblDocContent) lblDocContent.innerText = docState.summaryText;
            if (rawOcrText) rawOcrText.innerText = docState.rawText;

            if (data.audio_url) {
                playAudio(data.audio_url, () => {
                    updateDocAudioButtonUI();
                });
            } else {
                updateDocAudioButtonUI();
            }
            return;
        }

        // Lưu trữ cả 2 trạng thái: Nguyên văn (100% trích xuất từ ảnh) và Bản tóm tắt
        docState.rawText = data.raw_text || data.plain_speech_text || "Không phát hiện được văn bản trong ảnh.";
        
        // Trích xuất bản tóm tắt sẵn có ngay từ lượt quét (0ms trễ khi xem tóm tắt)
        const bullets = [];
        for (let i = 1; i <= 6; i++) {
            if (data[`bullet_${i}`]) bullets.push(data[`bullet_${i}`]);
        }
        const headline = data.headline || "Tóm tắt ý chính";
        const bulletText = bullets.length > 0 ? "• " + bullets.join("\n\n• ") : (data.all_bullets || data.plain_speech_text || docState.rawText);
        docState.summaryText = `📌 ${headline.toUpperCase()}\n════════════════════════════════════════\n\n${bulletText}`;

        // Chuẩn bị văn bản đọc tóm tắt sạch sẽ (không đọc các ký tự bullet trang trí)
        const rawSpeech = data.summary_speech || (headline + ". " + bullets.join(". ")) || data.plain_speech_text || bulletText;
        docState.summarySpeechText = rawSpeech.replace(/[•═📌]/g, '').trim();
        docState.hasSummarized = true;

        docState.isSummaryView = false;
        currentAudioUrl = null;
        currentWarningAudioUrl = null;

        setScreen('result');
        medicineDisplayBox.style.display = 'none';
        docDisplayBox.style.display = 'flex';
        resultBadge.style.display = 'none';
        if (btnChupTiepBottom) btnChupTiepBottom.innerText = "📸 BẤM ĐỂ CHỤP VĂN BẢN MỚI";
        window.scrollTo({ top: 0, behavior: 'smooth' });

        if (lblDocContent) lblDocContent.innerText = docState.rawText;
        if (rawOcrText) rawOcrText.innerText = docState.rawText;

        // Reset các nút công cụ văn bản
        if (textDocToggle) textDocToggle.innerText = "Thu gọn / Tóm tắt ý chính";
        if (iconDocToggle) iconDocToggle.innerText = "✨";

        updateDocAudioButtonUI();
    }

    // SỰ KIỆN NÚT CHUYỂN ĐỔI: THU GỌN / TÓM TẮT <-> XEM LẠI VĂN BẢN GỐC
    if (btnDocToggleSummary) {
        btnDocToggleSummary.addEventListener('click', async () => {
            if (!docState.rawText) return;

            // DỪNG TẤT CẢ ÂM THANH NGAY LẬP TỨC ĐỂ TRÁNH XUNG ĐỘT GIỮA 2 TAB
            stopAllAudio();

            if (!docState.isSummaryView) {
                // CHUYỂN SANG BẢN TÓM TẮT Ý CHÍNH (ĐÃ CÓ SẴN 0ms)
                docState.isSummaryView = true;

                if (!docState.hasSummarized) {
                    if (lblDocContent) lblDocContent.innerText = "⏳ Đang tóm tắt các ý chính dễ hiểu theo chuẩn Dyslexia...";
                    if (lblDocModeLabel) lblDocModeLabel.innerText = "⏳ Đang tạo bản tóm tắt...";
                    if (textDocToggle) textDocToggle.innerText = "Đang xử lý...";
                    btnDocToggleSummary.disabled = true;

                    try {
                        const sumData = await client.summarizeText(docState.rawText, currentSpeed);
                        const bList = sumData.bullet_points || [];
                        const hLine = sumData.headline || "Tóm tắt ý chính";
                        const bText = bList.length > 0 ? "• " + bList.join("\n\n• ") : (sumData.plain_speech_text || docState.rawText);

                        docState.summaryText = `📌 ${hLine.toUpperCase()}\n════════════════════════════════════════\n\n${bText}`;
                        docState.summarySpeechText = (sumData.plain_speech_text || (hLine + ". " + bList.join(". ")) || bText).replace(/[•═📌]/g, '').trim();
                        docState.hasSummarized = true;
                    } catch (err) {
                        alert("Không thể tóm tắt: " + err.message);
                        docState.isSummaryView = false;
                        btnDocToggleSummary.disabled = false;
                        updateDocAudioButtonUI();
                        return;
                    } finally {
                        btnDocToggleSummary.disabled = false;
                    }
                }

                if (lblDocModeLabel) lblDocModeLabel.innerText = "✨ BẢN TÓM TẮT Ý CHÍNH DỄ HIỂU";
                if (resultBadge) resultBadge.innerText = "✨ BẢN TÓM TẮT Ý CHÍNH DỄ HIỂU";
                if (lblDocContent) lblDocContent.innerText = docState.summaryText;

                if (textDocToggle) textDocToggle.innerText = "Xem lại văn bản gốc";
                if (iconDocToggle) iconDocToggle.innerText = "📄";

                updateDocAudioButtonUI();
            } else {
                // CHUYỂN NGƯỢC LẠI XEM VĂN BẢN GỐC 100%
                docState.isSummaryView = false;

                if (lblDocModeLabel) lblDocModeLabel.innerText = "📖 VĂN BẢN NGUYÊN VĂN (100%)";
                if (resultBadge) resultBadge.innerText = "📖 VĂN BẢN NGUYÊN VĂN (100%)";
                if (lblDocContent) lblDocContent.innerText = docState.rawText;

                if (textDocToggle) textDocToggle.innerText = "Thu gọn / Tóm tắt ý chính";
                if (iconDocToggle) iconDocToggle.innerText = "✨";

                updateDocAudioButtonUI();
            }
        });
    }

    // ==========================================================
    // TRA CỨU NHANH THEO TÊN
    // ==========================================================
    btnSearchMed.addEventListener('click', () => {
        const q = medSearchInput.value.trim();
        if (q) searchMedicineByName(q);
    });

    medSearchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const q = medSearchInput.value.trim();
            if (q) searchMedicineByName(q);
        }
    });

    quickChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const name = chip.getAttribute('data-name');
            medSearchInput.value = name;
            searchMedicineByName(name);
        });
    });

    async function loadDynamicQuickChips() {
        try {
            const resp = await fetch('/api/v1/medicine/list');
            if (!resp.ok) return;
            const resData = await resp.json();
            const meds = resData.data || [];
            if (!Array.isArray(meds) || meds.length === 0) return;

            const chipsContainer = document.querySelector('.quick-chips');
            if (!chipsContainer) return;

            const validMeds = meds.filter(m => m && m.name && m.name.trim()).slice(0, 6);
            if (validMeds.length === 0) return;

            chipsContainer.innerHTML = '<span class="chips-label">Thuốc mẫu chuẩn CSDL:</span>';
            validMeds.forEach(m => {
                const btn = document.createElement('button');
                btn.className = 'med-chip';
                btn.setAttribute('data-name', m.name);
                btn.textContent = `💊 ${m.name}`;
                btn.addEventListener('click', () => {
                    medSearchInput.value = m.name;
                    searchMedicineByName(m.name);
                });
                chipsContainer.appendChild(btn);
            });
        } catch (e) {
            console.warn('Không thể nạp danh mục thuốc động:', e);
        }
    }
    loadDynamicQuickChips();

    async function searchMedicineByName(name) {
        stopAllAudio();
        setScreen('loading');
        const loadingTitle = document.getElementById('loading-title');
        const loadingSub = document.getElementById('loading-sub');
        loadingTitle.innerText = `Đang tìm thuốc "${name}"...`;
        loadingSub.innerText = "Đối chiếu thông tin và sinh giọng đọc";

        try {
            const data = await client.recognizeMedicineText(name, true);
            const med = data.medicine || {};
            const audio = data.audio || {};
            const warningAudio = data.warning_audio || {};

            renderMedicineStep1({
                found_in_db: data.found_in_db,
                is_medicine: true,
                image_token: null,
                name: med.name,
                meal_timing: med.meal_timing,
                dosage_adult: med.dosage_adult,
                dosage_child: med.dosage_child,
                indication: med.indication,
                warning: med.warning,
                active_ingredient: med.active_ingredient,
                audio_url: audio.full_audio_url || audio.audio_url,
                warning_audio_url: warningAudio.full_audio_url || warningAudio.audio_url
            });
        } catch (err) {
            alert(`Lỗi tra cứu: ${err.message}`);
            setScreen('action');
        }
    }

    // ==========================================================
    // ĐIỀU KHIỂN ÂM THANH (AUDIO PLAYBACK)
    // ==========================================================
    function playAudio(url, onStart) {
        if (!url) return;
        audioPlayer.src = url;
        audioPlayer.playbackRate = currentSpeed;
        audioPlayer.play()
            .then(() => {
                audioPlayer.playbackRate = currentSpeed;
                if (onStart) onStart();
            })
            .catch(e => {
                console.log("Trình duyệt yêu cầu bấm để phát:", e);
                if (iconNgheLai) iconNgheLai.innerText = "🔊";
                if (textNgheLai) {
                    textNgheLai.innerText = currentMode === 'thuoc' ? "BẤM ĐỂ NGHE LẠI" : (docState.isSummaryView ? "NGHE ĐỌC TÓM TẮT" : "NGHE ĐỌC TOÀN VĂN");
                }
            });
    }

    function stopAllAudio() {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        if (currentMode === 'vanban') {
            docState.rawWantsPlay = false;
            docState.summaryWantsPlay = false;
            updateDocAudioButtonUI();
        } else {
            if (iconNgheLai) iconNgheLai.innerText = "🔊";
            if (textNgheLai) textNgheLai.innerText = "BẤM ĐỂ NGHE LẠI";
            if (iconLuuY) iconLuuY.innerText = "🔔";
            if (textLuuY) {
                textLuuY.innerText = (currentWarningAudioUrl && !btnLuuYThuoc.disabled) ? "Nghe lại lưu ý" : "Nghe lưu ý";
            }
        }
    }

    function enableWarningButton() {
        if (!currentWarningAudioUrl) return;
        btnLuuYThuoc.disabled = false;
        btnLuuYThuoc.classList.add('active-glow');
        if (iconLuuY) iconLuuY.innerText = "🔔";
        if (textLuuY) textLuuY.innerText = "Nghe lưu ý";
    }

    audioPlayer.addEventListener('ended', () => {
        if (currentMode === 'vanban') {
            docState.rawWantsPlay = false;
            docState.summaryWantsPlay = false;
            updateDocAudioButtonUI();
            return;
        }
        if (iconNgheLai) iconNgheLai.innerText = "🔊";
        if (textNgheLai) textNgheLai.innerText = "BẤM ĐỂ NGHE LẠI";
        if (iconLuuY) iconLuuY.innerText = "🔔";
        if (currentMode === 'thuoc') {
            if (currentWarningAudioUrl && audioPlayer.src.includes(currentWarningAudioUrl)) {
                if (textLuuY) textLuuY.innerText = "Nghe lại lưu ý";
            } else {
                enableWarningButton();
            }
        }
    });

    btnNgheLai.addEventListener('click', async () => {
        // Nếu âm thanh đang phát -> bấm nút là dừng ngay lập tức
        if (!audioPlayer.paused && audioPlayer.currentTime > 0) {
            stopAllAudio();
            return;
        }

        if (currentMode === 'thuoc') {
            if (currentAudioUrl) {
                playAudio(currentAudioUrl, () => {
                    if (iconNgheLai) iconNgheLai.innerText = "⏹";
                    if (textNgheLai) textNgheLai.innerText = "ĐANG ĐỌC HƯỚNG DẪN...";
                });
            }
        } else {
            // ==========================================
            // CHẾ ĐỘ VĂN BẢN: STREAM TRỰC TIẾP LƯU VÀO RAM ĐIỆN THOẠI
            // ==========================================
            if (docState.isSummaryView) {
                // ĐANG Ở TAB TÓM TẮT Ý CHÍNH
                if (docState.summaryLoading) return;

                // Nếu trong RAM đã có sẵn blob VÀ tốc độ khớp -> Phát lại tức thì (0ms)!
                if (docState.summaryBlobUrl && docState.summarySpeed === currentSpeed) {
                    playAudio(docState.summaryBlobUrl, () => {
                        updateDocAudioButtonUI();
                    });
                    return;
                }

                const textToRead = docState.summarySpeechText || docState.summaryText.replace(/^[^\n]*\n═+[^\n]*\n\n/, '').replace(/[•═📌]/g, '');
                if (!textToRead || !textToRead.trim()) return;

                docState.summaryLoading = true;
                updateDocAudioButtonUI();

                try {
                    if (docState.summaryBlobUrl) {
                        try { URL.revokeObjectURL(docState.summaryBlobUrl); } catch (e) {}
                        docState.summaryBlobUrl = null;
                    }

                    const blob = await client.fetchAudioStreamBlob(textToRead, currentSpeed);
                    docState.summaryBlobUrl = URL.createObjectURL(blob);
                    docState.summarySpeed = currentSpeed;
                    docState.summaryLoading = false;

                    playAudio(docState.summaryBlobUrl, () => {
                        updateDocAudioButtonUI();
                    });
                } catch (err) {
                    console.error("Lỗi stream audio tóm tắt:", err);
                    docState.summaryLoading = false;
                    updateDocAudioButtonUI();
                    alert("Không thể tải giọng đọc tóm tắt. Vui lòng thử lại!");
                }
            } else {
                // ĐANG Ở TAB TOÀN VĂN GỐC (100%)
                if (docState.rawLoading) return;

                // Nếu trong RAM đã có sẵn blob VÀ tốc độ khớp -> Phát lại tức thì (0ms)!
                if (docState.rawBlobUrl && docState.rawSpeed === currentSpeed) {
                    playAudio(docState.rawBlobUrl, () => {
                        updateDocAudioButtonUI();
                    });
                    return;
                }

                const textToRead = docState.rawText;
                if (!textToRead || !textToRead.trim()) return;

                docState.rawLoading = true;
                updateDocAudioButtonUI();

                try {
                    if (docState.rawBlobUrl) {
                        try { URL.revokeObjectURL(docState.rawBlobUrl); } catch (e) {}
                        docState.rawBlobUrl = null;
                    }

                    const blob = await client.fetchAudioStreamBlob(textToRead, currentSpeed);
                    docState.rawBlobUrl = URL.createObjectURL(blob);
                    docState.rawSpeed = currentSpeed;
                    docState.rawLoading = false;

                    playAudio(docState.rawBlobUrl, () => {
                        updateDocAudioButtonUI();
                    });
                } catch (err) {
                    console.error("Lỗi stream audio toàn văn:", err);
                    docState.rawLoading = false;
                    updateDocAudioButtonUI();
                    alert("Không thể tải giọng đọc toàn văn. Vui lòng thử lại!");
                }
            }
        }
    });

    btnLuuYThuoc.addEventListener('click', () => {
        if (!currentWarningAudioUrl || btnLuuYThuoc.disabled) return;
        if (!audioPlayer.paused && audioPlayer.src.includes(currentWarningAudioUrl)) {
            stopAllAudio();
        } else {
            playAudio(currentWarningAudioUrl, () => {
                if (iconLuuY) iconLuuY.innerText = "⏹";
                if (textLuuY) textLuuY.innerText = "ĐANG ĐỌC LƯU Ý...";
            });
        }
    });

    btnDungDoc.addEventListener('click', stopAllAudio);

    function applySpeed(speed) {
        const newSpeed = parseFloat(speed) || 1.0;
        const speedChanged = (Math.abs(newSpeed - currentSpeed) > 0.01);
        currentSpeed = newSpeed;

        speedPills.forEach(pill => {
            if (Math.abs(parseFloat(pill.dataset.speed) - currentSpeed) < 0.05) {
                pill.classList.add('active');
            } else {
                pill.classList.remove('active');
            }
        });

        // 1. Cập nhật ngay lập tức cho HTML5 audio đang phát
        if (audioPlayer) {
            audioPlayer.playbackRate = currentSpeed;
        }

        // 2. Nếu người dùng chọn mode tốc độ mới trong tab Văn bản:
        // Giải phóng cache RAM để lượt bấm nghe tiếp theo sẽ stream chuẩn ngữ điệu Edge-TTS mới
        if (speedChanged && currentMode === 'vanban') {
            revokeDocBlobs();
            updateDocAudioButtonUI();
        }

        localStorage.setItem('medidocx_speed', currentSpeed);
    }

    const savedSpeed = parseFloat(localStorage.getItem('medidocx_speed')) || 1.0;
    applySpeed(savedSpeed);

    speedPills.forEach(pill => {
        pill.addEventListener('click', () => {
            applySpeed(pill.dataset.speed);
        });
    });

    // ==========================================================
    // CÀI ĐẶT TRỢ NĂNG MODAL
    // ==========================================================
    btnInfoToggle.addEventListener('click', () => {
        infoModal.style.display = 'flex';
        checkAndDisplayServerStatus();
    });

    [btnCloseInfo, btnCloseInfoFooter].forEach(btn => {
        if (btn) btn.addEventListener('click', () => {
            infoModal.style.display = 'none';
        });
    });

    // ==========================================================
    // CẤU HÌNH & KIỂM TRA SERVER API (HỖ TRỢ GITHUB PAGES)
    // ==========================================================
    const serverUrlInput = document.getElementById('server-url-input');
    const btnSaveServerUrl = document.getElementById('btn-save-server-url');
    const serverStatusPill = document.getElementById('server-status-pill');
    const serverStatusMsg = document.getElementById('server-status-msg');
    const serverAlertBanner = document.getElementById('server-alert-banner');
    const btnOpenServerConfig = document.getElementById('btn-open-server-config');

    if (serverUrlInput) {
        serverUrlInput.value = client.baseURL;
    }

    async function checkAndDisplayServerStatus() {
        if (!serverStatusPill) return;
        serverStatusPill.textContent = "Đang thử...";
        serverStatusPill.style.background = "#fef3c7";
        serverStatusPill.style.color = "#92400e";

        const res = await client.checkHealth();
        if (res.ok) {
            serverStatusPill.textContent = "🟢 Đã kết nối";
            serverStatusPill.style.background = "#dcfce7";
            serverStatusPill.style.color = "#166534";
            if (serverStatusMsg) {
                serverStatusMsg.innerHTML = `Đang kết nối tới: <strong style="color: #16a34a;">${client.baseURL}</strong>`;
            }
            if (serverAlertBanner) {
                serverAlertBanner.style.display = "none";
            }
        } else {
            serverStatusPill.textContent = "🔴 Mất kết nối";
            serverStatusPill.style.background = "#fee2e2";
            serverStatusPill.style.color = "#991b1b";
            if (serverStatusMsg) {
                serverStatusMsg.innerHTML = `<span style="color: #dc2626;">Không kết nối được: ${res.detail || 'Lỗi mạng hoặc CORS'}.</span> Hãy chắc chắn server đang bật và link có https://`;
            }
            const isGitHubPages = window.location.hostname.endsWith('github.io');
            if (isGitHubPages || client.baseURL.includes('localhost') || client.baseURL.includes('127.0.0.1')) {
                if (serverAlertBanner) {
                    serverAlertBanner.style.display = "flex";
                }
            }
        }
    }

    if (btnSaveServerUrl) {
        btnSaveServerUrl.addEventListener('click', async () => {
            let url = (serverUrlInput.value || '').trim();
            if (!url) {
                url = window.location.origin;
            }
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                url = 'https://' + url;
                serverUrlInput.value = url;
            }
            client.setBaseURL(url);
            await checkAndDisplayServerStatus();
        });
    }

    if (btnOpenServerConfig) {
        btnOpenServerConfig.addEventListener('click', () => {
            infoModal.style.display = 'flex';
            if (serverUrlInput) serverUrlInput.focus();
        });
    }

    // Tự động kiểm tra kết nối ngay khi tải trang
    setTimeout(checkAndDisplayServerStatus, 500);

    // ==========================================================
    // CHAT PANEL — Trò chuyện 2 chiều về thuốc
    // ==========================================================

    const chatPanel       = document.getElementById('chat-panel');
    const chatMessages    = document.getElementById('chat-messages');
    const chatPanelDrugName = document.getElementById('chat-panel-drug-name');
    const chatInput       = document.getElementById('chat-input');
    const btnChatSend     = document.getElementById('btn-chat-send');
    const btnCloseChat    = document.getElementById('btn-close-chat');
    const btnOpenChat     = document.getElementById('btnOpenChat');
    const chatQuickQuestions = document.getElementById('chat-quick-questions');

    /** Mở chat panel và cập nhật context thuốc hiện tại */
    function openChatPanel(drugName, context) {
        chatState.context = context || {};
        chatState.isOpen = true;

        // Cập nhật tên thuốc trên header
        if (chatPanelDrugName) {
            chatPanelDrugName.textContent = drugName ? `Hỏi về: ${drugName}` : 'Hỏi về thuốc';
        }

        // Reset chat nếu đây là thuốc mới (context khác)
        if (chatMessages) {
            chatMessages.innerHTML = `
                <div class="chat-welcome">
                    <span class="chat-welcome-icon">💊</span>
                    <p>Bạn có thể hỏi tôi bất cứ điều gì về <strong>${drugName || 'loại thuốc này'}</strong>!</p>
                    <div class="chat-quick-questions" id="chat-quick-questions">
                        <button class="chat-quick-btn">Thuốc này có tác dụng phụ gì?</button>
                        <button class="chat-quick-btn">Có được dùng cho trẻ em không?</button>
                        <button class="chat-quick-btn">Uống khi nào trong ngày?</button>
                        <button class="chat-quick-btn">Tương tác với thuốc khác không?</button>
                    </div>
                </div>`;
            // Gắn lại event cho quick-question buttons mới render
            chatMessages.querySelectorAll('.chat-quick-btn').forEach(btn => {
                btn.addEventListener('click', () => sendChatMessage(btn.textContent));
            });
        }
        chatState.history = [];

        if (chatPanel) chatPanel.style.display = 'flex';
        if (chatInput) chatInput.focus();
    }

    /** Đóng chat panel và dừng stream nếu đang chạy */
    function closeChatPanel() {
        chatState.isOpen = false;
        if (chatState.abortController) {
            chatState.abortController.abort();
            chatState.abortController = null;
        }
        if (chatPanel) chatPanel.style.display = 'none';
    }

    /** Thêm bubble tin nhắn vào khung chat */
    function appendBubble(role, text) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'chat-avatar';
        avatar.textContent = role === 'user' ? '👤' : '💊';

        const textEl = document.createElement('div');
        textEl.className = 'chat-text';
        textEl.textContent = text;

        bubble.appendChild(avatar);
        bubble.appendChild(textEl);
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return textEl; // Trả về để append token khi stream
    }

    /** Thêm typing indicator (3 chấm nhảy) */
    function appendTypingIndicator() {
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble assistant';
        bubble.id = 'chat-typing-indicator';
        bubble.innerHTML = `
            <div class="chat-avatar">💊</div>
            <div class="chat-text chat-typing">
                <span></span><span></span><span></span>
            </div>`;
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return bubble;
    }

    /** Gửi tin nhắn và stream câu trả lời về */
    async function sendChatMessage(message) {
        if (!message || !message.trim() || chatState.isStreaming) return;

        // Ẩn welcome screen và quick questions sau lần hỏi đầu tiên (ẩn bằng style, KHÔNG xoá DOM để tránh lỗi click ngoài)
        const welcome = chatMessages.querySelector('.chat-welcome');
        if (welcome) welcome.style.display = 'none';

        const userMsg = message.trim();
        appendBubble('user', userMsg);

        if (chatInput) { chatInput.value = ''; chatInput.style.height = 'auto'; }
        if (btnChatSend) btnChatSend.disabled = true;
        chatState.isStreaming = true;

        // Thêm typing indicator trong khi chờ token đầu tiên
        const typingEl = appendTypingIndicator();

        // Bubble assistant (sẽ được lấp đầy bởi stream)
        let assistantTextEl = null;
        let fullReply = '';
        let cursorEl = null;
        let firstToken = true;

        chatState.abortController = client.streamChatMedicine({
            message: userMsg,
            history: chatState.history,
            context: chatState.context,

            onToken(token) {
                if (firstToken) {
                    // Token đầu tiên: xoá typing indicator, tạo bubble thật
                    typingEl.remove();
                    assistantTextEl = appendBubble('assistant', '');
                    // Thêm con trỏ nhấp nháy
                    cursorEl = document.createElement('span');
                    cursorEl.className = 'chat-cursor';
                    assistantTextEl.appendChild(cursorEl);
                    firstToken = false;
                }
                fullReply += token;
                // Chèn token trước con trỏ
                if (cursorEl) {
                    assistantTextEl.insertBefore(document.createTextNode(token), cursorEl);
                } else {
                    assistantTextEl.textContent += token;
                }
                chatMessages.scrollTop = chatMessages.scrollHeight;
            },

            onDone() {
                // Xoá con trỏ nhấp nháy khi stream xong
                if (cursorEl) cursorEl.remove();
                // Nếu chưa có bubble (server lỗi trước token đầu)
                if (firstToken) typingEl.remove();

                // Lưu lịch sử hội thoại
                chatState.history.push({ role: 'user', content: userMsg });
                chatState.history.push({ role: 'assistant', content: fullReply });

                // Giữ tối đa 20 lượt (10 cặp) để không vượt token limit
                if (chatState.history.length > 20) {
                    chatState.history = chatState.history.slice(-20);
                }

                chatState.isStreaming = false;
                chatState.abortController = null;
                if (btnChatSend) btnChatSend.disabled = false;
                if (chatInput) chatInput.focus();
            },

            onError(err) {
                if (cursorEl) cursorEl.remove();
                typingEl.remove();
                appendBubble('assistant', `⚠️ Có lỗi: ${err.message}`);
                chatState.isStreaming = false;
                chatState.abortController = null;
                if (btnChatSend) btnChatSend.disabled = false;
            }
        });
    }

    // --- Event listeners của chat ---
    if (btnCloseChat) btnCloseChat.addEventListener('click', closeChatPanel);

    if (btnChatSend) {
        btnChatSend.addEventListener('click', () => sendChatMessage(chatInput?.value));
    }

    if (chatInput) {
        // Gửi bằng Enter (Shift+Enter = xuống dòng)
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage(chatInput.value);
            }
        });
        // Tự điều chỉnh chiều cao textarea
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + 'px';
        });
    }

    // Quick questions được gắn event trong openChatPanel (re-render mỗi lần mở)

    // Ngăn chặn sự kiện click bên trong panel lan ra ngoài document
    if (chatPanel) {
        chatPanel.addEventListener('click', (e) => e.stopPropagation());
    }

    // Nút "💬 Hỏi thêm" trong thanh audio result
    if (btnOpenChat) {
        btnOpenChat.addEventListener('click', (e) => {
            e.stopPropagation();
            const drugName = lblTenThuoc?.textContent || '';
            const ctx = {
                medicine_name: lblTenThuoc?.textContent || '',
                indication: lblCongDung?.textContent || '',
                dosage_adult: lblLieuNguoiLon?.textContent || '',
                dosage_child: lblLieuTreEm?.textContent || '',
                timing: lblThoiDiem?.textContent || '',
                warnings: lblLuuYChiTiet?.textContent || '',
                active_ingredient: (lblHoatChat?.textContent || '').replace('Hoạt chất: ', ''),
                source: 'DB',
            };
            openChatPanel(drugName, ctx);
        });
    }

    // Hiển thị nút "Hỏi thêm" khi đang xem kết quả thuốc, ẩn khi ở tab văn bản
    function syncChatButtonVisibility() {
        if (!btnOpenChat) return;
        const isResultVisible = resultCard && resultCard.style.display !== 'none';
        const isMedicineMode = currentMode === 'thuoc';
        btnOpenChat.style.display = (isResultVisible && isMedicineMode) ? 'flex' : 'none';
    }

    // Observer theo dõi result-card hiện/ẩn để toggle nút chat
    if (resultCard && btnOpenChat) {
        new MutationObserver(() => syncChatButtonVisibility())
            .observe(resultCard, { attributes: true, attributeFilter: ['style'] });
    }

    // Đóng chat khi click ra bên ngoài khung chat (dùng composedPath an toàn với DOM mutations)
    document.addEventListener('click', (e) => {
        if (!chatState.isOpen || !chatPanel) return;
        const path = e.composedPath ? e.composedPath() : [];
        if (path.includes(chatPanel) || (btnOpenChat && path.includes(btnOpenChat))) {
            return;
        }
        closeChatPanel();
    });
});

