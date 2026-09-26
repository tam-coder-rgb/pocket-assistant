const appContainer = document.getElementById('appContainer');
const btnChangeFont = document.getElementById('btnChangeFont');
const btnZoomText = document.getElementById('btnZoomText');
const tabMedicine = document.getElementById('tabMedicine');
const tabText = document.getElementById('tabText');
const sectionMedicine = document.getElementById('sectionMedicine');
const sectionText = document.getElementById('sectionText');
const textContent = document.getElementById('textContent');
const btnPlayAudio = document.getElementById('btnPlayAudio');
const cameraInput = document.getElementById('cameraInput');
const galleryInput = document.getElementById('galleryInput');
const statusMessage = document.getElementById('appStatus');
const btnSearch = document.getElementById('btnSearch');
const searchInput = document.getElementById('searchInput');

// Use the Firebase Web app configuration from Firebase Console, never a service-account key.
const firebaseConfig = {
  apiKey: "AIzaSyC-Y_26ksseRhhfIWAZE9fiVvGB5ErzTmY",
  authDomain: "tro-ly-1ea29.firebaseapp.com",
  projectId: "tro-ly-1ea29",
  storageBucket: "tro-ly-1ea29.firebasestorage.app",
  messagingSenderId: "196843133476",
  appId: "1:196843133476:web:bdbff27c6848632308d6b1",
  measurementId: "G-BN45GE8J7B"
};

function showStatus(message) {
    statusMessage.textContent = message;
}

function selectTab(showText) {
    sectionMedicine.hidden = showText;
    sectionText.hidden = !showText;
    tabMedicine.classList.toggle('active', !showText);
    tabMedicine.classList.toggle('inactive', showText);
    tabText.classList.toggle('active', showText);
    tabText.classList.toggle('inactive', !showText);
    tabMedicine.setAttribute('aria-selected', String(!showText));
    tabText.setAttribute('aria-selected', String(showText));
}

tabMedicine.addEventListener('click', () => selectTab(false));
tabText.addEventListener('click', () => selectTab(true));

btnChangeFont.addEventListener('click', () => {
    const enabled = appContainer.classList.toggle('font-dyslexia');
    btnChangeFont.setAttribute('aria-pressed', String(enabled));
});

let zoomLevel = 0;
btnZoomText.addEventListener('click', () => {
    appContainer.classList.remove('zoom-1', 'zoom-2');
    zoomLevel = (zoomLevel + 1) % 3;
    if (zoomLevel) appContainer.classList.add(`zoom-${zoomLevel}`);
    btnZoomText.setAttribute('aria-label', `Cỡ chữ ${zoomLevel + 1} trên 3`);
});

function findVietnameseVoice() {
    return window.speechSynthesis.getVoices().find((voice) => voice.lang.toLowerCase().startsWith('vi'));
}

btnPlayAudio.addEventListener('click', () => {
    const text = textContent.value.trim();
    if (!text) {
        showStatus('Vui lòng nhập nội dung cần đọc.');
        return;
    }
    if (!('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined') {
        showStatus('Trình duyệt này không hỗ trợ đọc văn bản.');
        return;
    }

    if (window.speechSynthesis.speaking) {
        window.speechSynthesis.cancel();
        showStatus('Đã dừng đọc.');
        return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'vi-VN';
    const vietnameseVoice = findVietnameseVoice();
    if (vietnameseVoice) {
        utterance.voice = vietnameseVoice;
    }
    utterance.onstart = () => showStatus('Đang đọc văn bản.');
    utterance.onend = () => showStatus('Đã đọc xong.');
    utterance.onerror = (event) => {
        console.error('Lỗi giọng đọc:', event.error);
        showStatus(`Không phát được giọng đọc (${event.error}). Kiểm tra giọng tiếng Việt và âm lượng trên điện thoại.`);
    };

    window.speechSynthesis.speak(utterance);
    showStatus(vietnameseVoice
        ? 'Đang khởi động giọng đọc tiếng Việt.'
        : 'Đang thử giọng mặc định. Nếu không có tiếng, hãy cài giọng tiếng Việt trong cài đặt điện thoại.');
});

document.getElementById('btnCamera').addEventListener('click', () => cameraInput.click());
document.getElementById('btnGallery').addEventListener('click', () => galleryInput.click());
document.getElementById('btnScanText').addEventListener('click', () => cameraInput.click());

for (const input of [cameraInput, galleryInput]) {
    input.addEventListener('change', () => {
        if (input.files.length) {
            showStatus(`Đã chọn ảnh: ${input.files[0].name}. Chức năng quét chữ từ ảnh chưa được cấu hình.`);
        }
    });
}

btnSearch.addEventListener('click', async () => {
    const medicineName = searchInput.value.trim();
    if (!medicineName) {
        showStatus('Vui lòng nhập tên thuốc cần tìm.');
        searchInput.focus();
        return;
    }
    if (!firebaseConfig.apiKey || !firebaseConfig.appId) {
        showStatus('Chưa cấu hình Firebase Web. Lấy apiKey và appId trong Firebase Console rồi điền vào app.js.');
        return;
    }

    const originalLabel = btnSearch.innerHTML;
    btnSearch.disabled = true;
    btnSearch.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang xử lý...';

    let unsubscribe;
    let timeoutId;
    try {
        const [{ initializeApp, getApps, getApp }, { getFirestore, collection, addDoc, onSnapshot, doc }] = await Promise.all([
            import('https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js'),
            import('https://www.gstatic.com/firebasejs/10.8.1/firebase-firestore.js')
        ]);
        const firebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig);
        const db = getFirestore(firebaseApp);
        const request = await addDoc(collection(db, 'YeuCauXuLy'), {
            status: 'dang_cho',
            type: 'nhan_dien_thuoc',
            noi_dung: medicineName
        });

        await new Promise((resolve, reject) => {
            timeoutId = window.setTimeout(() => reject(new Error('Quá thời gian chờ máy chủ xử lý.')), 60000);
            unsubscribe = onSnapshot(doc(db, 'YeuCauXuLy', request.id), (snapshot) => {
                const data = snapshot.data();
                if (data?.status === 'hoan_thanh') {
                    textContent.value = data.ket_qua_text || 'Máy chủ không trả về nội dung.';
                    selectTab(true);
                    showStatus('Đã nhận kết quả tra cứu.');
                    resolve();
                } else if (data?.status === 'loi') {
                    reject(new Error(data.ket_qua_text || 'Máy chủ không xử lý được yêu cầu.'));
                }
            }, reject);
        });
    } catch (error) {
        console.error('Lỗi tra cứu Firebase:', error);
        showStatus(`Không thể tra cứu: ${error.message}`);
    } finally {
        window.clearTimeout(timeoutId);
        if (unsubscribe) unsubscribe();
        btnSearch.innerHTML = originalLabel;
        btnSearch.disabled = false;
    }
});