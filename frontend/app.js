const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const fs = require('fs');

const app = express();
const PORT = 3000;

// Middleware to parse form data
app.use(bodyParser.urlencoded({ extended: true }));

// Path to the users data file
const usersFilePath = path.join(__dirname, 'data', 'users.json');

// Create data directory if it doesn't exist
const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir);
}

// Create users.json if it doesn't exist
if (!fs.existsSync(usersFilePath)) {
    fs.writeFileSync(usersFilePath, JSON.stringify([], null, 2));
}

// Function to read users from file
function readUsers() {
    try {
        const data = fs.readFileSync(usersFilePath, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        console.error('Error reading users file:', error);
        return [];
    }
}

// Function to write users to file
function writeUsers(users) {
    try {
        fs.writeFileSync(usersFilePath, JSON.stringify(users, null, 2));
    } catch (error) {
        console.error('Error writing users file:', error);
    }
}

// Serve static files from the "public" folder
app.use(express.static(path.join(__dirname, 'public')));

// Serve the landing page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

// Serve the login page
app.get('/login', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'login.html'));
});

// Serve the signup page
app.get('/signup', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'signup.html'));
});

// Handle signup form submission
app.post('/signup', (req, res) => {
  const { name, email, password, confirmPassword } = req.body;

  // Check if passwords match
  if (password !== confirmPassword) {
    return res.send('Passwords do not match. <a href="/signup">Try again</a>');
  }

  // Read existing users
  const users = readUsers();

  // Check if user already exists
  const userExists = users.find((user) => user.email === email);
  if (userExists) {
    return res.send('Account with this email already exists. <a href="/login">Login here</a>');
  }

  // Save the new user
  users.push({ name, email, password });
  writeUsers(users);
  console.log('New user:', { name, email }); // For debugging

  // Redirect to login page
  res.redirect('/login');
});

// Handle login form submission
app.post('/login', (req, res) => {
  const { email, password } = req.body;

  // Read users from file
  const users = readUsers();

  // Find the user
  const user = users.find((user) => user.email === email);

  // Check if user exists
  if (!user) {
    return res.send('Account with this email does not exist. <a href="/signup">Signup here</a>');
  }

  // Check if password is correct
  if (user.password !== password) {
    return res.send('Wrong password. <a href="/login">Try again</a>');
  }

  // Redirect to chat interface
  res.redirect('/chat');
});

// Serve the chat interface
app.get('/chat', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'chat.html'));
});

// Serve edit profile page
app.get('/edit-profile', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'edit-profile.html'));
});

// Add this to your app.js (usually near other GET routes)
app.get('/settings', (req, res) => {
  res.sendFile(path.join(__dirname, 'views', 'settings.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});