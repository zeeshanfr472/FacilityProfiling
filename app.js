const API_URL = "https://facilityprofilingupdated.onrender.com";

document.addEventListener('DOMContentLoaded', () => {
    // Modal logic
    const modal = document.getElementById('modal');
    const closeModal = document.getElementById('closeModal');
    if (closeModal) {
        closeModal.onclick = () => { modal.style.display = 'none'; };
    }
    window.onclick = function(event) {
        if (event.target == modal) modal.style.display = 'none';
    }
});

// Field info modal popup
function showFieldInfo(field) {
    let text = "";
    switch(field) {
        case "username": text = "Unique username for login. Only letters and numbers."; break;
        case "password": text = "Password must be secure. At least 8 characters."; break;
        // add more field info as needed
        default: text = "No information available.";
    }
    document.getElementById('modalText').innerText = text;
    document.getElementById('modal').style.display = "block";
}

// Register
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.onsubmit = async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const res = await fetch(`${API_URL}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        document.getElementById('registerMsg').innerText = JSON.stringify(data);
    }
}

// Login
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.onsubmit = async (e) => {
        e.preventDefault();
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        const res = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        const data = await res.json();
        if (data.access_token) {
            localStorage.setItem('token', data.access_token);
            window.location.href = "index.html";
        } else {
            document.getElementById('loginMsg').innerText = "Login failed";
        }
    }
}

// You can expand this file with more JS for CRUD operations for inspections, token auth headers, etc.
// Ask if you need code for checklist CRUD with popups for every field!
