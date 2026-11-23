/**
 * VOICE INPUT — Ghi âm câu hỏi để gửi lên server nhận diện (Groq Whisper).
 *
 * Module chỉ lo việc ghi âm; nhận diện chữ do `transcribe(blob, filename)` (api_client) làm,
 * việc gửi tin nhắn do app.js quyết định qua onText.
 * - Tự dừng khi người dùng im lặng một lúc (người lớn tuổi không cần bấm "Dừng").
 * - Đo âm lượng: micro không thu được tiếng thì KHÔNG gửi (Whisper sẽ "bịa" câu khi nghe im lặng)
 *   và báo cho người dùng kiểm tra micro.
 * - Vòng sáng quanh nút to/nhỏ theo giọng nói (biến CSS --voice-level 0..1) để biết máy đang nghe.
 *
 * createVoiceInput({ button, transcribe, onText, onStateChange, onError }) → { stop, supported }
 * Trạng thái: 'idle' | 'listening' | 'processing'
 */
(function () {
    const SPEECH_LEVEL = 0.01;          // biên độ đỉnh (0-1) trên mức này = có tiếng
    const SPEECH_MIN_MS = 250;          // có tiếng cộng dồn chừng này mới tính là đã nói
    const SILENCE_MS = 2000;            // đã nói rồi im lặng liên tục chừng này -> tự dừng
    const NO_SPEECH_TIMEOUT_MS = 8000;  // bấm xong mà mãi không nghe tiếng -> dừng, báo kiểm tra micro
    const MAX_RECORD_MS = 30000;        // ghi tối đa
    const TICK_MS = 50;

    const MIME_CANDIDATES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'];
    const MIC_CONSTRAINTS = {
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
    };

    const MSG_NO_SPEECH = 'Micro không thu được tiếng nói. Hãy kiểm tra micro (đã bật, đúng thiết bị) '
        + 'rồi bấm "Nói" và nói to, gần máy hơn.';
    const MSG_NOT_UNDERSTOOD = 'Chưa nghe rõ câu hỏi. Hãy bấm "Nói" và nói lại chậm, rõ hơn.';

    function pickMimeType() {
        return MIME_CANDIDATES.find((t) => MediaRecorder.isTypeSupported(t)) || '';
    }

    function extensionOf(mime) {
        if (mime.includes('mp4')) return 'mp4';
        if (mime.includes('ogg')) return 'ogg';
        return 'webm';
    }

    function describeMicError(err) {
        if (err && (err.name === 'NotAllowedError' || err.name === 'SecurityError')) {
            return 'Bạn chưa cho phép dùng micro. Hãy bật quyền micro cho trang web này.';
        }
        if (err && err.name === 'NotFoundError') return 'Không tìm thấy micro trên thiết bị.';
        return 'Không mở được micro. Hãy thử lại.';
    }

    /**
     * Theo dõi âm lượng micro. Trả về { heardSpeech(), reliable(), maxLevel(), close() }.
     * reliable() = false khi trình duyệt không đo được (khi đó vẫn gửi âm thanh như bình thường).
     */
    function createLevelMeter(stream, { onLevel, onSilenceAfterSpeech, onNoSpeech }) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (!AudioCtx) return { heardSpeech: () => true, reliable: () => false, maxLevel: () => 0, close() {} };

        const ctx = new AudioCtx();
        ctx.resume().catch(() => {}); // có thể bị "suspended" vì đã qua await getUserMedia
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 1024;
        ctx.createMediaStreamSource(stream).connect(analyser);
        const data = new Uint8Array(analyser.fftSize);

        const startedAt = Date.now();
        let speechMs = 0;
        let silentSince = null;
        let max = 0;
        let ran = false;

        const timer = setInterval(() => {
            if (ctx.state !== 'running') return;
            ran = true;
            analyser.getByteTimeDomainData(data);
            let peak = 0;
            for (const v of data) peak = Math.max(peak, Math.abs(v - 128) / 128);
            max = Math.max(max, peak);
            onLevel(Math.min(1, peak / 0.3));

            if (peak > SPEECH_LEVEL) {
                speechMs += TICK_MS;
                silentSince = null;
            } else if (speechMs >= SPEECH_MIN_MS) {
                silentSince = silentSince ?? Date.now();
                if (Date.now() - silentSince >= SILENCE_MS) onSilenceAfterSpeech();
            }
            if (speechMs < SPEECH_MIN_MS && Date.now() - startedAt >= NO_SPEECH_TIMEOUT_MS) onNoSpeech();
        }, TICK_MS);

        return {
            heardSpeech: () => speechMs >= SPEECH_MIN_MS,
            reliable: () => ran,
            maxLevel: () => max,
            close() {
                clearInterval(timer);
                onLevel(0);
                ctx.close().catch(() => {});
            },
        };
    }

    function createVoiceInput({ button, transcribe, onText, onStateChange, onError }) {
        const supported = !!(button && navigator.mediaDevices?.getUserMedia && window.MediaRecorder);
        if (!supported) {
            if (button) button.style.display = 'none'; // vẫn gõ chữ bình thường
            return { stop() {}, supported: false };
        }

        let state = 'idle';
        let recorder = null;
        let stream = null;
        let meter = null;
        let chunks = [];
        let maxTimer = null;
        let cancelled = false;

        const report = (msg) => { if (onError) onError(msg); };

        function setState(next) {
            state = next;
            button.classList.toggle('listening', next === 'listening');
            button.classList.toggle('processing', next === 'processing');
            button.disabled = next === 'processing';
            button.setAttribute('aria-pressed', String(next === 'listening'));
            button.title = next === 'listening' ? 'Bấm để dừng nói' : 'Bấm để nói câu hỏi';
            if (onStateChange) onStateChange(next);
        }

        function releaseMic() {
            clearTimeout(maxTimer);
            if (meter) meter.close();
            if (stream) stream.getTracks().forEach((t) => t.stop());
            stream = null;
        }

        async function handleRecorded(mime, heard) {
            if (cancelled) return setState('idle');
            if (!heard || !chunks.length) {
                setState('idle');
                return report(MSG_NO_SPEECH);
            }
            setState('processing');
            try {
                const blob = new Blob(chunks, { type: mime || 'audio/webm' });
                const text = ((await transcribe(blob, `voice.${extensionOf(mime)}`)) || '').trim();
                setState('idle');
                if (text) onText(text);
                else report(MSG_NOT_UNDERSTOOD);
            } catch (err) {
                setState('idle');
                report(err.message || 'Không nhận diện được giọng nói. Hãy thử lại.');
            }
        }

        async function start() {
            cancelled = false;
            chunks = [];
            try {
                stream = await navigator.mediaDevices.getUserMedia(MIC_CONSTRAINTS);
            } catch (err) {
                return report(describeMicError(err));
            }
            const mime = pickMimeType();
            recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
            recorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
            recorder.onstop = () => {
                // Không đo được âm lượng -> không chặn, cứ gửi (server vẫn lọc câu Whisper bịa)
                const heard = !meter.reliable() || meter.heardSpeech();
                console.debug('[voice] max level', meter.maxLevel().toFixed(3), 'heard', heard);
                releaseMic();
                handleRecorded(recorder.mimeType || mime, heard);
            };
            meter = createLevelMeter(stream, {
                onLevel: (lvl) => button.style.setProperty('--voice-level', lvl.toFixed(2)),
                onSilenceAfterSpeech: stop,
                onNoSpeech: stop,
            });
            recorder.start();
            maxTimer = setTimeout(stop, MAX_RECORD_MS);
            setState('listening');
        }

        function stop() {
            if (recorder && recorder.state !== 'inactive') recorder.stop();
        }

        /** Huỷ hẳn (vd. đóng khung chat): không gửi âm thanh đi nhận diện. */
        function cancel() {
            cancelled = true;
            stop();
        }

        button.addEventListener('click', (e) => {
            e.stopPropagation();
            if (state === 'listening') stop();
            else if (state === 'idle') start();
        });

        return { stop: cancel, supported: true };
    }

    window.createVoiceInput = createVoiceInput;
})();
