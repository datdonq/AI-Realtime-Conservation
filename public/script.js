// public/script.js
const messagesDiv = document.getElementById('messages');
const inputField = document.getElementById('input');
const sendBtn = document.getElementById('sendBtn');
const recordBtn = document.getElementById('recordBtn');

// Kết nối tới WebSocket server
const ws = new WebSocket('ws://localhost:8592/ws/22'); // Thay 'your_session_id' bằng ID phiên của bạn nếu cần

ws.binaryType = 'arraybuffer'; // Để nhận dữ liệu nhị phân từ server

ws.onopen = () => {
  console.log('Đã kết nối tới server');
};

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
        addMessage(`You: ${message.substring(12)}`);

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

// Hàm xử lý hàng đợi từ
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
function addMessageTypingEffect(message, delay = 10, callback) {
  if (!currentMessageElement) {
    // Tạo phần tử mới nếu chưa có
    currentMessageElement = document.createElement('div');
    currentMessageElement.textContent = 'AI: '; // Bắt đầu với nhãn "AI: "
    messagesDiv.appendChild(currentMessageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight; // Tự động cuộn xuống khi có tin nhắn mới
  }

  let index = 0;

  function typeCharacter() {
    if (index < message.length) {
      currentMessageElement.textContent += message.charAt(index);
      index++;
      messagesDiv.scrollTop = messagesDiv.scrollHeight; // Tự động cuộn xuống theo từng ký tự
      setTimeout(typeCharacter, delay); // Điều chỉnh thời gian giữa các ký tự
    } else if (callback) {
      callback(); // Gọi callback sau khi gõ xong từ
    }
  }

  // Bắt đầu hiệu ứng gõ từng ký tự
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
    messageElement.textContent = message;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    currentMessageElement = null; // Đặt lại phần tử hiển thị của AI
    
    resetWordQueue(); // Reset hàng đợi khi người dùng gửi tin nhắn mới
  }

// Gửi tin nhắn văn bản
sendBtn.addEventListener('click', () => {
    const message = inputField.value.trim();
    if (message) {
      addMessage(`You: ${message}`);
      currentMessageElement = null; // Đặt lại phần tử hiển thị của AI
    
      resetWordQueue(); // Reset hàng đợi khi người dùng gửi tin nhắn mới
      clearAudioQueue(); // Xóa hàng đợi âm thanh khi gửi tin nhắn mới
      ws.send(message);
      inputField.value = '';
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
