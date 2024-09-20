// public/script.js
const messagesDiv = document.getElementById('messages');
const inputField = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');
const recordBtn = document.getElementById('recordBtn');

// Kết nối tới WebSocket server
const ws = new WebSocket('ws://localhost:8592/ws/22'); // Thay 'your_session_id' bằng ID phiên của bạn nếu cần
// Gửi tin nhắn ping để giữ cho kết nối WebSocket sống
let pingInterval;
ws.binaryType = 'arraybuffer'; // Để nhận dữ liệu nhị phân từ server

ws.onopen = () => {
  console.log('Đã kết nối tới server');
  pingInterval = setInterval(() => {
    ws.send('ping'); // Gửi tin nhắn ping đến server
  }, 30000); // 30 giây (có thể thay đổi nếu cần)
};
// ws.send(''); // Gửi tin nhắn bắt đầu kết nối
// Khai báo biến để tích lũy phản hồi từ AI
let aiMessageBuffer = '';
let currentMessageElement = null; // Giữ phần tử hiện tại để nối thêm nội dung
let wordQueue = []; // Hàng đợi để lưu các từ nhận được từ WebSocket
let isTyping = false; // Cờ để xác định có đang gõ một từ hay không
ws.onmessage = (event) => {
    if (typeof event.data === 'string') {
      // Xử lý tin nhắn văn bản
      const message = event.data;
      if (message.startsWith('[start]')) {
        // Lời chào
        const greeting = message.substring(7);
        addMessageTypingEffect(`${greeting}`);
      } else if (message.startsWith('[end=')) {
        aiMessageBuffer = ''; // Xóa bộ đệm sau khi hiển thị
      } else if (message.startsWith('[+]You said')) {
        // Phản hồi từ người dùng
        addMessage(`${message.substring(12)}`);

        currentMessageElement = null; // Đặt lại phần tử
      } else if (message.startsWith('[end]')) {

      } else if (message.startsWith('[end start]')) {
        
      }else {
        // // Tin nhắn phản hồi từ AI
        // aiMessageBuffer += message;
        // addMessageTypingEffect(`${message}`);
        addWordToQueue(message);
      }
    } else {
      // Xử lý dữ liệu nhị phân (âm thanh)
      const audioData = event.data;
      enqueueAudio(audioData); // Thêm vào hàng đợi âm thanh
    }
  };
  
 // Hàm để thêm từ vào hàng đợi
function addWordToQueue(word) {
  wordQueue.push(word); // Thêm từ vào hàng đợi
  if (!isTyping) {
    processWordQueue(); // Bắt đầu xử lý hàng đợi nếu không có gì đang được gõ
  }
}

function processWordQueue() {
  if (wordQueue.length === 0) {
    isTyping = false; // Không có từ nào để gõ
    return;
  }

  isTyping = true; // Đang gõ từ

  const word = wordQueue.shift(); // Lấy từ đầu tiên từ hàng đợi

  addMessageTypingEffect(word, 30, () => {
    // Khi gõ từ xong, tiếp tục gõ từ tiếp theo
    processWordQueue();
  });
}

// Hàm hiệu ứng gõ từng từ
// Hàm hiển thị tin nhắn với hiệu ứng gõ chữ (tin nhắn từ AI)
// Hàm hiển thị tin nhắn với hiệu ứng gõ chữ (tin nhắn từ AI)
function addMessageTypingEffect(message, delay = 100, callback) {
  let index = 0;

  // Nếu chưa có phần tử hiện tại thì tạo mới, nếu đã có thì tiếp tục nối vào phần tử hiện tại
  if (!currentMessageElement) {
    currentMessageElement = document.createElement('div');
    currentMessageElement.classList.add('message', 'agent'); // Phân biệt tin nhắn từ AI với lớp 'agent'
    currentMessageElement.textContent = ''; // Nội dung ban đầu
    messagesDiv.appendChild(currentMessageElement); // Thêm vào div #messages
  }

  // Cuộn xuống cuối khung chat
  messagesDiv.scrollTop = messagesDiv.scrollHeight;

  // Hàm gõ từng ký tự
  function typeCharacter() {
    if (index < message.length) {
      currentMessageElement.textContent += message.charAt(index); // Nối từng ký tự vào tin nhắn hiện tại
      index++;
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
      setTimeout(typeCharacter, delay); // Điều chỉnh thời gian giữa các ký tự
    } else {
      if (callback) callback(); // Gọi callback khi hoàn thành
    }
  }

  // Bắt đầu gõ ký tự
  typeCharacter();
}


// Reset hàng đợi từ và dừng hiệu ứng gõ
function resetWordQueue() {
  wordQueue = []; // Xóa toàn bộ từ trong hàng đợi
  isTyping = false; // Dừng trạng thái gõ hiện tại
  if (currentMessageElement) {
    currentMessageElement = null; // Đặt lại phần tử hiện tại của AI
  }
}
// Hàm hiển thị tin nhắn thông thường (không hiệu ứng gõ)
function addMessage(message) {
  const messageElement = document.createElement('div');
  messageElement.classList.add('message', 'you'); // Phân biệt tin nhắn từ người dùng với lớp 'you'
  messageElement.textContent = `${message}`; // Nội dung tin nhắn từ người dùng
  currentMessageElement = null; // Đặt lại phần tử hiển thị của AI
  document.getElementById('messages').appendChild(messageElement); // Thêm vào div #messages
  document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight; // Cuộn xuống cuối
}

// Gửi tin nhắn văn bản bằng nút send hoặc phím Enter
// Gửi tin nhắn văn bản bằng nút send hoặc phím Enter
function sendMessage() {
  const message = inputField.value.trim();
  if (message) {
    addMessage(`${message}`);
    currentMessageElement = null; // Đặt lại phần tử hiển thị của AI
    
    resetWordQueue(); // Reset hàng đợi khi người dùng gửi tin nhắn mới

    if (isPlaying) {
      clearAudioQueue(); // Dừng âm thanh đang phát nếu có
    }

    ws.send(message); // Gửi tin nhắn đến WebSocket server
    inputField.value = ''; // Xóa nội dung trong trường nhập liệu
  }
}


// Xử lý khi nhấn nút gửi
sendBtn.addEventListener('click', () => {
  sendMessage(); // Gọi hàm gửi tin nhắn
});

// Xử lý khi nhấn phím Enter
inputField.addEventListener('keypress', (event) => {
  if (event.key === 'Enter') {
    event.preventDefault(); // Ngăn chặn hành vi mặc định của phím Enter
    sendMessage(); // Gọi hàm gửi tin nhắn
  }
});
// Hàng đợi âm thanh và biến kiểm soát
let audioQueue = [];
let isPlaying = false;
let currentAudio = null; // Biến để lưu âm thanh đang phát

// Thêm âm thanh vào hàng đợi
function enqueueAudio(audioData) {
  audioQueue.push(audioData);
  if (!isPlaying) {
    playNextAudio();
  }
}

// Phát âm thanh tiếp theo trong hàng đợi
function playNextAudio() {
  if (audioQueue.length > 0) {
    isPlaying = true;
    const audioData = audioQueue.shift();
    playAudio(audioData);
  } else {
    isPlaying = false;
  }
}

// Phát âm thanh từ dữ liệu nhị phân
function playAudio(audioData) {
  const blob = new Blob([audioData], { type: 'audio/wav' }); // Thay đổi type nếu cần
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);

  currentAudio = audio; // Lưu âm thanh đang phát

  audio.onended = () => {
    URL.revokeObjectURL(url); // Giải phóng URL sau khi sử dụng
    currentAudio = null; // Xóa tham chiếu âm thanh hiện tại
    playNextAudio(); // Phát âm thanh tiếp theo
  };

  audio.play();
}

// Xóa hàng đợi âm thanh và dừng âm thanh đang phát
function clearAudioQueue() {
  audioQueue = [];
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
  isPlaying = false;
}

// Xử lý ghi âm giọng nói
let isRecording = false;
let mediaRecorder;
let audioChunks = [];

recordBtn.addEventListener('click', async () => {
  // Dừng phát âm thanh khi bắt đầu ghi âm
  if (isPlaying) {
    clearAudioQueue(); // Dừng âm thanh đang phát và xóa hàng đợi
  }

  if (isRecording) {
    mediaRecorder.stop();
    recordBtn.textContent = '🎤';
    isRecording = false;
  } else {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      alert('Trình duyệt của bạn không hỗ trợ ghi âm.');
      return;
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.start();
    recordBtn.textContent = '⏹️';
    isRecording = true;

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm; codecs=opus' });
      clearAudioQueue(); // Xóa hàng đợi âm thanh khi gửi âm thanh mới
      sendAudio(audioBlob);
      audioChunks = [];
    };
  }
});

// Gửi dữ liệu âm thanh tới server
function sendAudio(audioBlob) {
  // Đọc dữ liệu từ Blob và gửi qua WebSocket
  audioBlob.arrayBuffer().then((arrayBuffer) => {
    ws.send(arrayBuffer);
  });
}

// Xóa hàng đợi âm thanh và dừng âm thanh đang phát
function clearAudioQueue() {
  audioQueue = [];
  if (currentAudio) {
    currentAudio.pause(); // Dừng âm thanh đang phát
    currentAudio.currentTime = 0; // Đặt lại thời gian phát về 0
    currentAudio = null;
  }
  isPlaying = false;
}