/**
 * MOBILE API CLIENT SDK - TRỢ LÝ ĐỌC DYSLEXIA & NGƯỜI GIÀ
 * Sử dụng để tích hợp vào ứng dụng React Native, Flutter (WebView/Bridge), hoặc Mobile Web/PWA.
 */

class A11yMobileClient {
    constructor(baseURL = null) {
        if (!baseURL) {
            // 1. Nếu đang chạy trực tiếp trên máy tính (localhost) -> Luôn kết nối trực tiếp vào máy chủ nội bộ
            const isLocal = window.location.hostname === 'localhost' || 
                            window.location.hostname === '127.0.0.1' || 
                            window.location.hostname === '0.0.0.0';
            
            if (isLocal) {
                baseURL = window.location.origin;
            } 
            // 2. Khi chạy trên GitHub Pages: Ưu tiên link cố định từ file config.js
            else if (typeof MEDIDOCX_CONFIG !== 'undefined' && 
                     MEDIDOCX_CONFIG.SERVER_URL && 
                     !MEDIDOCX_CONFIG.SERVER_URL.includes('yourdomain.com')) {
                baseURL = MEDIDOCX_CONFIG.SERVER_URL;
            } 
            // 3. Cơ chế dự phòng khi test (tham số ?server= hoặc localStorage)
            else {
                try {
                    const urlParams = new URLSearchParams(window.location.search);
                    baseURL = urlParams.get('server') || localStorage.getItem('MEDIDOCX_SERVER_URL');
                } catch (e) {
                    // Ignore
                }
                if (!baseURL && typeof MEDIDOCX_CONFIG !== 'undefined') {
                    baseURL = MEDIDOCX_CONFIG.SERVER_URL;
                }
                if (!baseURL) {
                    baseURL = window.location.origin;
                }
            }
        }
        this.setBaseURL(baseURL);
    }

    setBaseURL(newURL) {
        this.baseURL = (newURL || window.location.origin).trim().replace(/\/$/, '');
        try {
            localStorage.setItem('MEDIDOCX_SERVER_URL', this.baseURL);
        } catch (e) {
            // Ignore
        }
    }

    /**
     * Kiểm tra tình trạng kết nối tới Server
     * @returns {Promise<{ok: boolean, status: string, detail?: string}>}
     */
    async checkHealth() {
        try {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), 4500);
            const res = await fetch(`${this.baseURL}/api/health`, {
                method: 'GET',
                signal: controller.signal
            });
            clearTimeout(timer);
            if (res.ok) {
                return { ok: true, status: 'connected' };
            }
            return { ok: false, status: 'error', detail: `Mã lỗi HTTP ${res.status}` };
        } catch (err) {
            return { ok: false, status: 'unreachable', detail: err.message || 'Không thể kết nối' };
        }
    }

    /**
     * Gửi ảnh từ Camera điện thoại lên Server để xử lý toàn bộ quy trình:
     * PaddleOCR + Vision LLM + Tóm tắt Dyslexia + Tạo âm thanh giọng đọc TTS.
     * @param {Blob|File} imageFile - File ảnh hoặc Blob từ Camera
     * @param {boolean} generateAudio - Có tạo file giọng đọc MP3 hay không
     * @returns {Promise<Object>} Kết quả phân tích và URL file âm thanh
     */
    async scanAndAnalyze(imageFile, generateAudio = true) {
        const formData = new FormData();
        formData.append('file', imageFile);
        formData.append('generate_audio', generateAudio);

        const response = await fetch(`${this.baseURL}/api/v1/process/full-pipeline`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Lỗi không xác định' }));
            throw new Error(err.detail || `Lỗi máy chủ (${response.status})`);
        }

        const data = await response.json();
        
        // Chuẩn hóa đường dẫn file âm thanh tuyệt đối
        if (data.audio && data.audio.audio_url) {
            data.audio.full_audio_url = `${this.baseURL}${data.audio.audio_url}`;
        }

        return data;
    }

    /**
     * Yêu cầu Server đọc một đoạn văn bản bất kỳ thành tiếng
     * @param {string} text - Văn bản cần đọc
     * @param {number} speed - Hệ số tốc độ (0.5x - 2.0x, mặc định 1.0)
     * @returns {string} URL luồng stream âm thanh trực tiếp
     */
    getAudioStreamUrl(text, speed = 1.0) {
        const speedQuery = speed ? `&speed=${speed}` : '';
        return `${this.baseURL}/api/v1/speech/stream?text=${encodeURIComponent(text)}${speedQuery}`;
    }

    /**
     * Tải luồng âm thanh dạng Blob vào RAM điện thoại (In-Memory Blob)
     * Tự động dùng POST nếu văn bản dài, truyền đúng tốc độ speed
     * @param {string} text - Văn bản cần đọc
     * @param {number} speed - Hệ số tốc độ (0.5x - 2.0x, mặc định 1.0)
     * @returns {Promise<Blob>} Dữ liệu nhị phân âm thanh trong RAM
     */
    async fetchAudioStreamBlob(text, speed = 1.0) {
        if (!text || !text.trim()) {
            throw new Error("Không có nội dung văn bản để đọc.");
        }

        let response;
        if (text.length < 500) {
            const url = this.getAudioStreamUrl(text, speed);
            response = await fetch(url);
        } else {
            response = await fetch(`${this.baseURL}/api/v1/speech/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, speed })
            });
        }

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(err.detail || `Lỗi tải âm thanh: ${response.status}`);
        }
        return await response.blob();
    }

    /**
     * Gửi ảnh vỏ hộp, vỉ thuốc hoặc đơn thuốc lên Server để nhận diện thuốc:
     * - Đối chiếu CSDL chuẩn (chính xác)
     * - Fallback gọi AI kèm cảnh báo tham khảo
     * - Tạo âm thanh giọng đọc
     * @param {Blob|File} imageFile - File ảnh từ Camera hoặc thư viện
     * @param {boolean} generateAudio - Có tạo file âm thanh MP3 hay không
     * @returns {Promise<Object>} Kết quả nhận diện thuốc và URL âm thanh
     */
    async recognizeMedicine(imageFile, generateAudio = true) {
        const formData = new FormData();
        formData.append('file', imageFile);
        formData.append('generate_audio', generateAudio);

        const response = await fetch(`${this.baseURL}/api/v1/medicine/recognize`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Lỗi không xác định' }));
            throw new Error(err.detail || `Lỗi máy chủ (${response.status})`);
        }

        const data = await response.json();
        if (data.audio && data.audio.audio_url) {
            data.audio.full_audio_url = `${this.baseURL}${data.audio.audio_url}`;
        }
        if (data.warning_audio && data.warning_audio.audio_url) {
            data.warning_audio.full_audio_url = `${this.baseURL}${data.warning_audio.audio_url}`;
        }
        return data;
    }

    /**
     * Tra cứu thông tin thuốc từ chuỗi tên thuốc (không cần chụp ảnh)
     * @param {string} textQuery - Tên thuốc (ví dụ: 'Panadol Cảm Cúm')
     * @param {boolean} generateAudio - Có tạo âm thanh giọng đọc không
     */
    async recognizeMedicineText(textQuery, generateAudio = true) {
        const response = await fetch(`${this.baseURL}/api/v1/medicine/recognize-text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: textQuery,
                generate_audio: generateAudio
            })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Lỗi không xác định' }));
            throw new Error(err.detail || `Lỗi máy chủ (${response.status})`);
        }

        const data = await response.json();
        if (data.audio && data.audio.audio_url) {
            data.audio.full_audio_url = `${this.baseURL}${data.audio.audio_url}`;
        }
        if (data.warning_audio && data.warning_audio.audio_url) {
            data.warning_audio.full_audio_url = `${this.baseURL}${data.warning_audio.audio_url}`;
        }
        return data;
    }

    /**
     * Lấy danh sách thuốc có sẵn trong Cơ sở dữ liệu CSDL
     */
    async listMedicines(q = '') {
        const url = q ? `${this.baseURL}/api/v1/medicine/list?q=${encodeURIComponent(q)}` : `${this.baseURL}/api/v1/medicine/list`;
        const response = await fetch(url);
        if (!response.ok) return { data: [] };
        return await response.json();
    }

    /**
     * Tạo âm thanh giọng đọc từ một đoạn văn bản ngắn bất kỳ
     * @param {string} text - Văn bản cần đọc
     * @param {number} speed - Hệ số tốc độ (0.5x - 2.0x, mặc định 1.0)
     */
    async synthesizeSpeech(text, speed = 1.0) {
        const response = await fetch(`${this.baseURL}/api/v1/speech/synthesize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, speed })
        });
        if (!response.ok) return null;
        const data = await response.json();
        if (data.audio_url) {
            data.full_audio_url = `${this.baseURL}${data.audio_url}`;
        }
        return data;
    }

    /**
     * Tóm tắt văn bản bằng AI (Chỉ chạy khi người dùng chủ động bấm Tóm tắt)
     * @param {string} text - Đoạn văn bản nguyên văn cần tóm tắt
     * @param {number} speed - Tốc độ đọc
     */
    async summarizeText(text, speed = 1.0) {
        const response = await fetch(`${this.baseURL}/api/v1/text/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, speed })
        });
        if (!response.ok) {
            throw new Error("Không thể tóm tắt văn bản.");
        }
        const res = await response.json();
        return res.data || res;
    }

    /**
     * Kiểm tra trạng thái tạo âm thanh giọng đọc ngầm (cho văn bản hoặc tóm tắt)
     * @param {string} token - Mã doc_token hoặc sum_token
     */
    async getDocAudioStatus(token) {
        if (!token) return { status: 'failed', audio_url: null };
        try {
            const response = await fetch(`${this.baseURL}/api/v1/process/audio-status?token=${encodeURIComponent(token)}`);
            if (!response.ok) return { status: 'generating', audio_url: null };
            const data = await response.json();
            if (data.audio_url && !data.audio_url.startsWith('http')) {
                data.audio_url = `${this.baseURL}${data.audio_url}`;
            }
            return data;
        } catch (e) {
            return { status: 'generating', audio_url: null };
        }
    }

    /**
     * Lấy thông tin mạng và trạng thái hệ thống
     */
    async getSystemInfo() {
        try {
            const response = await fetch(`${this.baseURL}/api/v1/system/info`);
            if (response.ok) return await response.json();
        } catch (e) {
            console.log("Không thể lấy system info:", e);
        }
        return null;
    }
    /**
     * Gửi ảnh sang endpoint App Inventor (Bước 1):
     * Tra cứu CSDL chuẩn tức thì, trả về token và trạng thái có cần phân tích AI hay không.
     * @param {Blob|File} imageFile
     * @param {number} speed
     */
    async recognizeMedicineAppInventor(imageFile, speed = 1.0) {
        const formData = new FormData();
        formData.append('file', imageFile);

        const speedQuery = speed ? `?speed=${speed}` : '';
        const response = await fetch(`${this.baseURL}/api/v1/medicine/app-inventor${speedQuery}`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Lỗi không xác định' }));
            throw new Error(err.detail || `Lỗi máy chủ (${response.status})`);
        }

        const data = await response.json();
        if (data.audio_url && !data.audio_url.startsWith('http')) {
            data.audio_url = `${this.baseURL}${data.audio_url}`;
        }
        if (data.warning_audio_url && !data.warning_audio_url.startsWith('http')) {
            data.warning_audio_url = `${this.baseURL}${data.warning_audio_url}`;
        }
        return data;
    }

    /**
     * Phân tích AI sâu khi người dùng bấm nút [BẤM ĐỂ PHÂN TÍCH AI] (Bước 2):
     * @param {string} token - Mã token của ảnh đã cache ở Bước 1
     * @param {number} speed
     */
    async analyzeMedicineAI(token, speed = 1.0) {
        const speedQuery = speed ? `&speed=${speed}` : '';
        const response = await fetch(`${this.baseURL}/api/v1/medicine/analyze-ai?token=${encodeURIComponent(token)}${speedQuery}`, {
            method: 'POST'
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: 'Lỗi phân tích AI' }));
            throw new Error(err.detail || `Lỗi phân tích AI (${response.status})`);
        }

        const data = await response.json();
        if (data.audio_url && !data.audio_url.startsWith('http')) {
            data.audio_url = `${this.baseURL}${data.audio_url}`;
        }
        if (data.warning_audio_url && !data.warning_audio_url.startsWith('http')) {
            data.warning_audio_url = `${this.baseURL}${data.warning_audio_url}`;
        }
        return data;
    }

    /**
     * Đọc văn bản tài liệu bằng endpoint App Inventor:
     * @param {Blob|File} imageFile
     * @param {number} speed
     */
    async processDocumentAppInventor(imageFile, speed = 1.0) {
        const formData = new FormData();
        formData.append('file', imageFile);

        const speedQuery = speed ? `?speed=${speed}` : '';
        const response = await fetch(`${this.baseURL}/api/v1/process/app-inventor${speedQuery}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            let msg = 'Lỗi đọc văn bản';
            if (response.status === 504 || response.status === 408) {
                msg = 'Hết thời gian chờ phản hồi (Timeout). Vui lòng thử lại.';
            } else if (response.status === 502 || response.status === 503) {
                msg = 'Máy chủ đang bận hoặc đường truyền ngrok bị gián đoạn.';
            }
            const err = await response.json().catch(() => ({ detail: msg }));
            throw new Error(err.detail || `${msg} (${response.status})`);
        }

        const data = await response.json();
        if (data.audio_url && !data.audio_url.startsWith('http')) {
            data.audio_url = `${this.baseURL}${data.audio_url}`;
        }
        return data;
    }

    // =========================================================================
    // CHAT API — Trò chuyện 2 chiều về thuốc với Streaming (SSE)
    // =========================================================================

    /**
     * Gửi câu hỏi về thuốc và nhận câu trả lời dạng stream (phun chữ từng token).
     *
     * @param {string}   message      - Câu hỏi của người dùng.
     * @param {Array}    history      - Lịch sử hội thoại [{role, content}, ...].
     * @param {Object}   context      - Thông tin thuốc từ màn hình kết quả.
     * @param {Function} onToken      - Callback nhận từng token text: (token: string) => void
     * @param {Function} onDone       - Callback khi stream kết thúc: () => void
     * @param {Function} onError      - Callback khi có lỗi: (err: Error) => void
     * @returns {AbortController}     - Trả về controller để huỷ stream nếu cần.
     */
    streamChatMedicine({ message, history = [], context = {}, onToken, onDone, onError }) {
        const controller = new AbortController();

        (async () => {
            try {
                const response = await fetch(`${this.baseURL}/api/v1/chat/medicine`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message, history, context }),
                    signal: controller.signal,
                });

                if (!response.ok) {
                    const err = await response.json().catch(() => ({ detail: `Lỗi HTTP ${response.status}` }));
                    throw new Error(err.detail || `Lỗi kết nối server (${response.status})`);
                }

                // Đọc stream SSE thủ công qua ReadableStream
                const reader = response.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });

                    // Mỗi SSE event kết thúc bằng "\n\n"
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop(); // Giữ lại phần chưa hoàn chỉnh

                    for (const line of lines) {
                        if (!line.startsWith('data: ')) continue;
                        const payload = line.slice(6); // Bỏ "data: "
                        if (payload === '[DONE]') {
                            try { await reader.cancel(); } catch (e) {}
                            if (onDone) onDone();
                            return;
                        }
                        // Khôi phục newline đã escape từ server
                        const token = payload.replace(/\\n/g, '\n');
                        if (onToken) onToken(token);
                    }
                }
                try { await reader.cancel(); } catch (e) {}
                if (onDone) onDone();
            } catch (err) {
                if (err.name === 'AbortError') return; // Người dùng chủ động huỷ — không báo lỗi
                if (onError) onError(err);
            }
        })();

        return controller; // Caller giữ controller để gọi controller.abort() khi cần
    }
}

// Xuất module cho cả môi trường CommonJS và Browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = A11yMobileClient;
}

