const express = require('express');
const path = require('path');
const app = express();

// Cấu hình để phục vụ các file tĩnh từ thư mục 'public'
app.use(express.static(path.join(__dirname, '/public')));

// Gửi file index.html khi truy cập vào '/'
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

const PORT = process.env.PORT || 3002;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
