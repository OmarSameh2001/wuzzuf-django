// mailer.js
const express = require("express");
const nodemailer = require("nodemailer");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

// Setup transporter (Gmail example)
const transporter = nodemailer.createTransport({
  service: "gmail",
  auth: {
    user: "hebagassem911@gmail.com",
    pass: "smue mdmk uoov zctr " // App password or real password (if less secure apps allowed)
  }
});

app.post("/send-otp", async (req, res) => {
  const { email, name } = req.body;
  const otp = Math.floor(100000 + Math.random() * 900000);

  console.log(`Sending OTP to: ${email} for ${name}`); // Debug log
  console.log(`Generated OTP: ${otp}`); // Debug log

  const mailOptions = {
    from: '"RecruitHub" <hebagassem911@gmail.com>',
    to: email,
    subject: "Your OTP Verification Code",
    text: `Dear ${name},\n\nYour One-Time Password (OTP) is: ${otp}\n\nThis code is valid for a short time. Please do not share it with anyone.\n\nBest regards,\nRecruitHub Team`
  };

  try {
    await transporter.sendMail(mailOptions);
    console.log(`OTP email sent successfully to: ${email}`); // Debug log
    res.json({ success: true, otp }); // Send back the OTP
  } catch (err) {
    console.error("Failed to send mail:", err);
    res.status(500).json({ success: false, message: "Email sending failed" });
  }
});

// Start server
const PORT = 5000;
app.listen(PORT, () => console.log(`Mailer server running on port ${PORT}`));
