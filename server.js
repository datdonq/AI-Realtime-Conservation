// server.js
const express = require('express');
const path = require('path');

const app = express();

// Phục vụ các tệp tĩnh trong thư mục 'public'
app.use(express.static(path.join(__dirname, 'public')));

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Frontend server is running on port ${PORT}`);
});
