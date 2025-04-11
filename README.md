go visit https://lofi.is-best.net/ but please don't judge me based on the website 
it just took me 40 min to set up
![image](https://github.com/user-attachments/assets/8c85e837-b4ac-4a56-8154-2f21ada12ac5)
here's the code for it 
``` python

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lofi Infinite</title>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@300;400;500&display=swap" rel="stylesheet">
    <link rel="icon" type="image/png" href="https://i.imgur.com/3QZQZQZ.png"> <!-- Add your favicon URL here -->
    <style>
        body {
            margin: 0;
            overflow: hidden;
            font-family: 'Fira Code', monospace;
            background: black;
            color: #33ff33;
        }
        .background {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            animation: fade 10s infinite alternate;
            z-index: -1;
        }
        @keyframes fade {
            0% { opacity: 0.8; }
            100% { opacity: 1; }
        }
        .overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.5);
            z-index: 0;
        }
        .top-left {
            position: fixed;
            top: 20px;
            left: 20px;
            font-size: 18px;
            z-index: 2;
        }
        .bottom-center {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            align-items: center;
            gap: 10px;
            z-index: 2;
        }
        .right-panel {
            position: fixed;
            right: 20px;
            top: 20px;
            width: 200px;
            background: rgba(0, 0, 0, 0.7);
            padding: 15px;
            border-radius: 10px;
            z-index: 2;
        }
        button {
            padding: 10px;
            margin: 5px;
            cursor: pointer;
            background: black;
            color: #33ff33;
            border: 1px solid #33ff33;
            border-radius: 5px;
            transition: background 0.3s, color 0.3s;
        }
        button:hover {
            background: #33ff33;
            color: black;
        }
        input[type="range"] {
            width: 100px;
            cursor: pointer;
        }
        .play-pause {
            font-size: 24px;
            cursor: pointer;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="background" id="bg"></div>
    <div class="overlay"></div>
    <div class="top-left">Listeners: <span id="listenerCount">0</span></div>
    <div class="bottom-center">
        <button onclick="prevTrack()">◄</button>
        <div class="play-pause" onclick="togglePlay()">▶</div>
        <button onclick="nextTrack()">►</button>
        <input type="range" id="volume" min="0" max="1" step="0.1" onchange="changeVolume()">
    </div>
    <div class="right-panel">
        <h3>About</h3>
        <p>Created by Your Name</p>
        <p>Shortcuts:</p>
        <ul>
            <li>Space - Play/Pause</li>
            <li>↑ ↓ - Volume Control</li>
            <li>← → - Change Track</li>
        </ul>
        <p>Contact: your@email.com</p>
    </div>
    <script>
        // Replace these with direct links to your audio files
        const musicFiles = [
            'https://raw.githubusercontent.com/chingsangamba/common-resouces/main/Solace%20Her%20-%20Ningsingdraba%20(Official%20Music%20Video)%20%20Neeru%20Thoudam%20%202022%20-%20Uchek%20Society.mp3',
            'https://raw.githubusercontent.com/chingsangamba/common-resouces/main/lofi-hip-hop-background-lofi-music-270003.mp3',
            'https://raw.githubusercontent.com/chingsangamba/common-resouces/main/lofi-song-room-by-lofium-242714.mp3',
            'https://raw.githubusercontent.com/chingsangamba/common-resouces/main/whispering-vinyl-loops-lofi-beats-281193.mp3'
        ];

        const gifs = [
            'https://i.imgur.com/6l18viu.gif',
            'https://i.imgur.com/RmnyTls.gif',
            'https://i.imgur.com/WUZuNui.gif',
            'https://i.imgur.com/tb59GS8.gif',
            'https://i.imgur.com/B8avEar.gif',
            'https://i.imgur.com/ampxFGK.gif',
            'https://i.imgur.com/196JsE1.gif',
            'https://i.imgur.com/0ZCKrbn.gif' // Add more GIFs as needed
        ];

        let currentTrackIndex = 0;
        let isPlaying = false;
        let audioElement;

        // Create audio element
        function createAudioElement(src) {
            let audio = new Audio(src);
            audio.loop = true;
            audio.volume = 0.5;
            return audio;
        }

        // Load and play a track
        function loadTrack(index) {
            if (audioElement) {
                audioElement.pause();
            }
            currentTrackIndex = index;
            audioElement = createAudioElement(musicFiles[currentTrackIndex]);
            audioElement.play()
                .then(() => {
                    isPlaying = true;
                    document.querySelector('.play-pause').textContent = '⏸';
                })
                .catch((error) => {
                    console.error("Audio playback failed:", error);
                    alert("Please interact with the page to start playback.");
                });
            changeBackground(); // Change background when track changes
        }

        // Play/Pause toggle
        function togglePlay() {
            if (!audioElement) {
                loadTrack(currentTrackIndex); // Load the track if it hasn't been loaded yet
            }
            if (isPlaying) {
                audioElement.pause();
                document.querySelector('.play-pause').textContent = '▶';
            } else {
                audioElement.play()
                    .then(() => {
                        document.querySelector('.play-pause').textContent = '⏸';
                    })
                    .catch((error) => {
                        console.error("Audio playback failed:", error);
                        alert("Please interact with the page to start playback.");
                    });
            }
            isPlaying = !isPlaying;
        }

        // Change volume
        function changeVolume() {
            let volume = document.getElementById("volume").value;
            audioElement.volume = volume;
        }

        // Next track (random selection)
        function nextTrack() {
            let nextIndex = Math.floor(Math.random() * musicFiles.length);
            loadTrack(nextIndex);
        }

        // Previous track (random selection)
        function prevTrack() {
            let prevIndex = Math.floor(Math.random() * musicFiles.length);
            loadTrack(prevIndex);
        }

        // Change background GIF
        function changeBackground() {
            let bg = document.getElementById("bg");
            let randomGif = gifs[Math.floor(Math.random() * gifs.length)];
            bg.style.backgroundImage = `url(${randomGif})`;
        }

        // Update listener count
        function updateListeners() {
            document.getElementById("listenerCount").innerText = Math.floor(Math.random() * 1000);
        }
        setInterval(updateListeners, 5000);

        // Keybindings
        document.addEventListener("keydown", function(event) {
            if (event.code === "Space") {
                togglePlay();
                event.preventDefault();
            } else if (event.code === "ArrowUp") {
                audioElement.volume = Math.min(1, audioElement.volume + 0.1);
            } else if (event.code === "ArrowDown") {
                audioElement.volume = Math.max(0, audioElement.volume - 0.1);
            } else if (event.code === "ArrowRight") {
                nextTrack();
            } else if (event.code === "ArrowLeft") {
                prevTrack();
            }
        });

        // Initialize
        changeBackground(); // Set initial background
    </script>
</body>
</html>
```
