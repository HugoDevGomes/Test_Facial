function captureFrame() {
    const video = document.getElementById('video-feed');
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg');
}

function login() {
    const imageDataURL = captureFrame();
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ image: imageDataURL })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('login-name').textContent = data.name;
        document.getElementById('login-timestamp').textContent = data.timestamp;
        document.getElementById('login-info').style.display = 'block';
        document.getElementById('register-details').style.display = 'none';
        document.getElementById('login-details').style.display = 'block';
    })
    .catch(error => {
        console.error('Error during login:', error);
    });
}

function showRegisterInput() {
    document.getElementById('login-info').style.display = 'block';
    document.getElementById('login-details').style.display = 'none';
    document.getElementById('register-details').style.display = 'block';
}

function confirmRegister() {
    const name = document.getElementById('register-name').value;
    if (name) {
        const imageDataURL = captureFrame();
        fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name: name, image: imageDataURL })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            document.getElementById('register-details').style.display = 'none';
            document.getElementById('login-details').style.display = 'block';
        })
        .catch(error => {
            console.error('Error during registration:', error);
        });
    }
}
