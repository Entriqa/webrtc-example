const express = require('express');
const multer = require('multer');
const path = require('path');

const app = express();
const port = 3000;

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, __dirname);
  },
  filename: function (req, file, cb) {
    cb(null, 'video/recorded_video.webm');
  }
});

const upload = multer({ storage: storage });

app.use(express.static(__dirname));


app.post('/upload', upload.single('video'), (req, res) => {
  res.send('File uploaded successfully');
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});