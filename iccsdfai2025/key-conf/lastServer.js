const express = require('express');
const jwt = require('json-web-token');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');
const bodyParser = require('body-parser');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.static(path.join(__dirname, 'public')));
const port = process.env.PORT

// Настроим body-parser для парсинга JSON и URL-encoded данных
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Load the keys from the file
const publicKeyPath = path.join(__dirname, 'public.pem');
const publicKey = fs.readFileSync(publicKeyPath, 'utf8');
const privateKeyPath = path.join(__dirname, 'private.pem');
const privateKey = fs.readFileSync(privateKeyPath, 'utf8');

// Подключаемся к SQLite
const db = new sqlite3.Database(path.join(__dirname, 'database.db'), (err) => {
    if (err) {
        console.error('Error connecting to SQLite database:', err);
    } else {
        console.log('Connected to SQLite database');
    }
});

const insertFlagParts = async () => {
    // First, check if the super_flag table already has records
    db.get('SELECT COUNT(*) as count FROM super_flag', (err, row) => {
        if (err) {
            console.error('Error checking super_flag table:', err);
            return;
        }

        // If the table has records (count > 0), skip insertion
        if (row.count > 0) {
            console.log('super_flag table already has records, skipping insertion.');
            return;
        }

        // Define the flag and split it into parts
        const flag = 'ICTF{0h_n000_jwttt_g1v3_m3_jwtttt}';
        const parts = [
            flag.slice(0, 5),   // 'ICTF{'
            flag.slice(5, 10),  // '0h_n0'
            flag.slice(10, 15), // '00_jw'
            flag.slice(15, 20), // 'ttt_g'
            flag.slice(20)      // '1v3_m3_jwtttt}'
        ];

        // Insert each part into the super_flag table
        parts.forEach((part, index) => {
            db.run(
                'INSERT INTO super_flag (part) VALUES (?)',
                [part],
                (err) => {
                    if (err) {
                        console.error(`Error inserting part ${index + 1}:`, err);
                    } else {
                        console.log(`Inserted part ${index + 1}: ${part}`);
                    }
                }
            );
        });
    });
};

// Function to insert 10 sample posts into the posts table if it's empty
const insertSamplePosts = () => {
    // First, check if the posts table already has records
    db.get('SELECT COUNT(*) as count FROM posts', (err, row) => {
        if (err) {
            console.error('Error checking posts table:', err);
            return;
        }

        // If the table has records (count > 0), skip insertion
        if (row.count > 0) {
            console.log('posts table already has records, skipping insertion.');
            return;
        }

        // Define 10 sample posts
        const samplePosts = [
            {
                title: 'The Rise of AI in 2025',
                subtitle: 'How AI is shaping the future',
                content: 'Artificial Intelligence has made significant strides in 2025, with applications ranging from healthcare to autonomous vehicles. This post explores the latest advancements and their impact on society.'
            },
            {
                title: 'JavaScript Frameworks to Watch',
                subtitle: 'Top 5 frameworks',
                content: 'JavaScript frameworks like React, Vue, and Svelte are dominating the web development scene. Here’s what you need to know about the top 5 frameworks in 2025.'
            },
            {
                title: 'Cybersecurity Tips for Beginners',
                subtitle: 'Protect your digital life',
                content: 'With cyber threats on the rise, beginners need to understand the basics of cybersecurity. Start with these practical tips to secure your online presence.'
            },
            {
                title: 'The Future of Quantum Computing',
                subtitle: 'What to expect',
                content: 'Quantum computing is no longer a distant dream. Experts predict it will revolutionize industries by 2035. Learn about the current state and future possibilities.'
            },
            {
                title: 'Getting Started with SQLite',
                subtitle: 'A lightweight database',
                content: 'SQLite is a great choice for small applications. Learn how to set it up and use it in your next project with this beginner-friendly guide.'
            },
            {
                title: 'Cloud Computing Trends in 2025',
                subtitle: 'What’s new in cloud tech',
                content: 'Cloud computing continues to evolve, with trends like serverless architecture and edge computing taking center stage. Here’s what’s new in 2025.'
            },
            {
                title: 'Building REST APIs with Express',
                subtitle: 'A beginner’s guide',
                content: 'Express.js makes it easy to build REST APIs. Follow this guide to create your first API in just a few steps, complete with examples.'
            },
            {
                title: 'The Impact of 5G on IoT',
                subtitle: 'Faster networks, smarter devices',
                content: '5G is revolutionizing the Internet of Things by enabling faster and more reliable connections. Discover how it’s transforming smart devices.'
            },
            {
                title: 'Why Open Source Matters',
                subtitle: 'The power of community',
                content: 'Open source software is driving innovation across industries. This post explores the benefits of open source and why community matters.'
            },
            {
                title: 'Introduction to Web3',
                subtitle: 'The decentralized future',
                content: 'Web3 promises a decentralized internet powered by blockchain technology. Learn the basics of Web3 and what it means for the future.'
            }
        ];

        // Insert each post into the posts table
        samplePosts.forEach((post, index) => {
            db.run(
                'INSERT INTO posts (title, subtitle, content) VALUES (?, ?, ?)',
                [post.title, post.subtitle, post.content],
                (err) => {
                    if (err) {
                        console.error(`Error inserting post ${index + 1}:`, err);
                    } else {
                        console.log(`Inserted post ${index + 1}: ${post.title}`);
                    }
                }
            );
        });
    });
};

// Create the posts table, users table, and super_flag table if they don't exist
const createTables = async () => {
    db.run(
        `CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )`, (err) => {
        if (err) throw err;
    }
    );

    db.run(
        `CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            subtitle TEXT,
            content TEXT
        )`, (err) => {
        if (err) throw err;
    }
    );

    db.run(
        `CREATE TABLE IF NOT EXISTS super_flag (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part TEXT
        )`, (err) => {
        if (err) throw err;
        insertFlagParts();
        insertSamplePosts();
    });
};

// Function to insert the flag parts into super_flag table if it's empty


// Execute table creation, flag insertion, and sample posts insertion
createTables();

// Helper function to generate JWT token
function generateToken(payload) {
    return new Promise((resolve, reject) => {
        jwt.encode(privateKey, payload, 'RS256', function (err, token) {
            if (err) reject(err);
            resolve(token);
        });
    });
}

// Middleware to verify the JWT token
function verifyToken(req, res, next) {
    const token = req.query.token;

    jwt.decode(publicKey, token, (err, decoded) => {
        if (err) {
            return res.status(401).json({ message: 'Token authentication failed' });
        }
        req.decoded = decoded;
        next();
    });
}

// Endpoint to generate a JWT token with admin: false or true
app.get('/generateToken', async (req, res) => {
    const payload = { admin: false, username: req.query.username };
    try {
        const token = await generateToken(payload);
        res.json({ token });
    } catch (err) {
        res.status(500).json({ message: 'Error generating token' });
    }
});

app.get('/api/checkToken', verifyToken, (req, res) => {
    res.json({ valid: true, user: req.decoded });
});

// Login endpoint
app.post('/login', (req, res) => {
    const { username, password } = req.body;

    // Check user existence in the database
    db.all('SELECT * FROM users WHERE username = ?', [username], (err, results) => {
        if (err) {
            return res.status(500).json({ message: 'Error checking user existence' });
        }
        if (results.length === 0) {
            return res.status(400).json({ message: 'User not found' });
        }

        const user = results[0];

        // Check if password matches (no hashing, as passwords are stored in plain text)
        if (user.password !== password) {
            return res.status(400).json({ message: 'Invalid credentials' });
        }

        const payload = { admin: false, username: username };
        generateToken(payload)
            .then(token => {
                res.json({ token });
            })
            .catch(err => {
                res.status(500).json({ message: 'Error generating token' });
            });
    });
});

app.post('/register', (req, res) => {
    const { username, password } = req.body;

    // Basic validation
    if (!username || !password) {
        return res.status(400).json({ message: 'Username and password are required' });
    }

    // Check if user already exists
    db.all('SELECT * FROM users WHERE username = ?', [username], (err, results) => {
        if (err) {
            return res.status(500).json({ message: 'Error checking existing user' });
        }

        if (results.length > 0) {
            return res.status(400).json({ message: 'Username already taken' });
        }

        // Insert new user into database (plain text password)
        db.run(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            [username, password],
            async (err) => {
                if (err) {
                    return res.status(500).json({ message: 'Error registering user' });
                }

                // Generate token for new user
                const payload = { admin: false, username: username };
                try {
                    const token = await generateToken(payload);
                    res.json({ token });
                } catch (err) {
                    res.status(500).json({ message: 'Error generating token' });
                }
            }
        );
    });
});

// Endpoint to check if the user is admin
app.get('/checkAdmin', verifyToken, (req, res) => {
    res.json(req.decoded);
});

// Endpoint to create a post (only for admin) - Vulnerable to SQL Injection
app.post('/createPost', verifyToken, (req, res) => {
    const { title, subtitle, content } = req.body;

    // Проверка, что только администратор может создавать посты
    if (req.decoded.admin !== true) {
        return res.status(403).json({ message: 'Admin access required to create post' });
    }

    // Уязвимость: SQL Injection due to string interpolation
    db.run(
        `INSERT INTO posts (title, subtitle, content) VALUES ('${title}', '${subtitle}', '${content}')`,
        (err) => {
            if (err) {
                console.log(err);
                return res.status(500).json({ message: 'Error creating post' });
            }
            res.status(201).json({ message: 'Post created' });
        }
    );
});

// Endpoint to get all posts
app.get('/api/posts', (req, res) => {
    db.all('SELECT * FROM posts', (err, rows) => {
        if (err) {
            return res.status(500).json({ message: 'Error retrieving posts' });
        }
        res.json(rows);
    });
});

// Endpoint to view a specific post by ID
app.get('/api/posts/:id', (req, res) => {
    const postId = req.params.id;

    db.all('SELECT * FROM posts WHERE id = ?', [postId], (err, rows) => {
        if (err) {
            return res.status(500).json({ message: 'Error retrieving post' });
        }
        if (rows.length === 0) {
            return res.status(404).json({ message: 'Post not found' });
        }
        res.json(rows[0]);
    });
});

// Start server
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});

// Close the database connection when the process exits
process.on('SIGINT', () => {
    db.close((err) => {
        if (err) {
            console.error('Error closing SQLite database:', err);
        }
        console.log('SQLite database connection closed');
        process.exit(0);
    });
});