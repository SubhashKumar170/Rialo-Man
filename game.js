    // =================== Part 1: Constants & Globals ===================
    const TILE = 25;
    const FPS = 60;
    const PLAYER_SPEED = 2.5;
    const GHOST_SPEED = 1.8;
    const LIVES = 2;
    const TURN_TOLERANCE = 6;

    let canvas, ctx;
    let mazeWidth, mazeHeight;
    let walls = [], pellets = [];
    let pelletRadius = 4;
    let player, ghosts = [];
    let score = 0;
    let lives = LIVES;
    let gameOver = false;
    let win = false;
    let keys = {};
    let entryPassed = false;
    let gameOverFrame = 0; // Animation frame counter

    // =================== Part 2: Maze Map ===================
    const MAZE_MAP = [
        "############################",
        "#............##............#",
        "#.####.#####.##.#####.####.#",
        "#.$..#.#   #.##.#   #.#..$.#",
        "#.####.#####.##.#####.####.#",
        "#..........................#",
        "#.####.##.########.##.####.#",
        "#.####.##.########.##.####.#",
        "#......##....##....##......#",
        "######.#####.##.#####.######",
        "     #.##          ##.#     ",
        "     #.##.###--###.##.#     ",
        "######.##.#$$$$$$#.#.##.######",
        "      .   #$$$$$$#   .      ",
        "######.##.#$$$$$$#.#.##.######",
        "     #.##.########.##.#     ",
        "     #.##..........##.#     ",
        "     #.##.########.##.#     ",
        "######.##.########.##.######",
        "#............##............#",
        "#.####.#####.##.#####.####.#",
        "#.$..##..............##..$.#",
        "###.##.##.########.##.##.###",
        "###.##.##.########.##.##.###",
        "#......##....##....##......#",
        "#.##########.##.##########.#",
        "#.##########.##.##########.#",
        "#..........P...............#",
        "############################"
    ];

    // =================== Part 3: Entry Code Screen ===================
    function entryScreen(callback) {
        let inputText = "";
        let frame = 0;
        const particles = [];

        for (let i = 0; i < 100; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                radius: Math.random() * 2 + 1,
                speed: Math.random() * 0.5 + 0.2
            });
        }

        function drawEntry() {
            frame++;
            ctx.fillStyle = "#0b0c1a";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            particles.forEach(p => {
                p.y -= p.speed;
                if (p.y < 0) p.y = canvas.height;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = "rgba(255,255,255,0.6)";
                ctx.fill();
            });

            ctx.fillStyle = "yellow";
            ctx.font = "40px 'Courier New', monospace";
            ctx.fillText("Enter Code:", 50, 80);

            ctx.font = "36px 'Courier New', monospace";
            ctx.shadowBlur = 20;
            ctx.shadowColor = "yellow";
            ctx.fillStyle = "yellow";
            ctx.fillText(inputText, 50, 140);

            if (Math.floor(frame / 30) % 2 === 0) {
                ctx.fillStyle = "yellow";
                ctx.fillRect(50 + ctx.measureText(inputText).width + 2, 120, 10, 36);
            }
            ctx.shadowBlur = 0;

            requestAnimationFrame(drawEntry);
        }

        document.addEventListener("keydown", function onKey(e) {
            if (e.key === "Enter") {
                if (inputText.toLowerCase() === "nagasai" || inputText.toLowerCase() === "rialo") {
                    entryPassed = true;
                    document.removeEventListener("keydown", onKey);
                    callback();
                } else {
                    inputText = "";
                }
            } else if (e.key === "Backspace") {
                inputText = inputText.slice(0, -1);
            } else if (e.key.length === 1) {
                inputText += e.key;
            }
        });

        drawEntry();
    }

    // =================== Part 4: Load Maze ===================
    function loadMaze() {
        walls = [];
        pellets = [];
        let playerPos = null;
        let ghostPositions = [];
        mazeHeight = MAZE_MAP.length;
        mazeWidth = MAZE_MAP[0].length;

        for (let r = 0; r < mazeHeight; r++) {
            for (let c = 0; c < mazeWidth; c++) {
                let ch = MAZE_MAP[r][c];
                let x = c * TILE;
                let y = r * TILE;

                if (ch === '#') {
                    walls.push({ x, y, width: TILE, height: TILE });
                } else if (ch === '.' || ch === '$') {
                    pellets.push({ x: x + TILE / 2, y: y + TILE / 2 });
                } else if (ch === 'P') {
                    playerPos = { x: x + TILE / 2, y: y + TILE / 2 };
                } else if (ch === 'G') {
                    ghostPositions.push({ x: x + TILE / 2, y: y + TILE / 2 });
                }
            }
        }

        if (!playerPos) playerPos = { x: 14 * TILE + TILE / 2, y: 23 * TILE + TILE / 2 };
        if (ghostPositions.length === 0) {
            ghostPositions = [
                { x: 13 * TILE + TILE / 2, y: 14 * TILE + TILE / 2 },
                { x: 14 * TILE + TILE / 2, y: 14 * TILE + TILE / 2 },
                { x: 15 * TILE + TILE / 2, y: 14 * TILE + TILE / 2 },
            ];
        }

        return { playerPos, ghostPositions };
    }

    // =================== Part 5: Helper ===================
    function rectFromCenter(x, y, size) {
        return { x: x - size / 2, y: y - size / 2, width: size, height: size };
    }

    function isColliding(rect, wallList) {
        for (let wall of wallList) {
            if (
                rect.x < wall.x + wall.width &&
                rect.x + rect.width > wall.x &&
                rect.y < wall.y + wall.height &&
                rect.y + rect.height > wall.y
            ) return true;
        }
        return false;
    }

    // =================== Part 6: Player & Ghost Classes ===================
    class Player {
        constructor(x, y, img) {
            this.x = x;
            this.y = y;
            this.radius = TILE / 2 - 2;
            this.dir = { x: 0, y: 0 };
            this.nextDir = { x: 0, y: 0 };
            this.speed = PLAYER_SPEED;
            this.img = img;
        }

        update() {
            if (keys["ArrowUp"]) this.nextDir = { x: 0, y: -1 };
            else if (keys["ArrowDown"]) this.nextDir = { x: 0, y: 1 };
            else if (keys["ArrowLeft"]) this.nextDir = { x: -1, y: 0 };
            else if (keys["ArrowRight"]) this.nextDir = { x: 1, y: 0 };

            const centerX = this.x % TILE;
            const centerY = this.y % TILE;
            const tolerance = Math.max(TURN_TOLERANCE, TILE / 4);
            const canTurn = Math.abs(centerX - TILE / 2) < tolerance && Math.abs(centerY - TILE / 2) < tolerance;

            if (canTurn) {
                const newX = this.x + this.nextDir.x * this.speed;
                const newY = this.y + this.nextDir.y * this.speed;
                const rectTry = rectFromCenter(newX, newY, this.radius * 2 - 2);
                if (!isColliding(rectTry, walls)) this.dir = this.nextDir;
            }

            let newX = this.x + this.dir.x * this.speed;
            let newY = this.y + this.dir.y * this.speed;

            if (newX < 0) newX = mazeWidth * TILE - this.radius;
            else if (newX > mazeWidth * TILE) newX = this.radius;
            newY = Math.max(this.radius, Math.min(newY, mazeHeight * TILE - this.radius));

            const rectTry = rectFromCenter(newX, newY, this.radius * 2 - 2);
            if (!isColliding(rectTry, walls)) {
                this.x = newX;
                this.y = newY;
            }
        }

        draw() {
            if (this.img) {
                ctx.save();
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.clip();
                ctx.drawImage(this.img, this.x - this.radius, this.y - this.radius, this.radius * 2, this.radius * 2);
                ctx.restore();
            } else {
                ctx.fillStyle = "yellow";
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }

    class Ghost {
        constructor(x, y, img) {
            this.x = x;
            this.y = y;
            this.radius = TILE / 2 - 3;
            this.speed = GHOST_SPEED;
            this.dir = [{ x: 1, y: 0 }, { x: -1, y: 0 }, { x: 0, y: 1 }, { x: 0, y: -1 }][Math.floor(Math.random() * 4)];
            this.img = img;
        }

        update() {
            let newX = this.x + this.dir.x * this.speed;
            let newY = this.y + this.dir.y * this.speed;
            const rectTry = rectFromCenter(newX, newY, this.radius * 2 - 2);
            if (!isColliding(rectTry, walls)) {
                this.x = newX;
                this.y = newY;
            } else this.chooseNewDir();
            if (Math.random() < 0.02) this.chooseNewDir();
        }

        chooseNewDir() {
            const options = [{ x: 1, y: 0 }, { x: -1, y: 0 }, { x: 0, y: 1 }, { x: 0, y: -1 }].filter(d => {
                let nx = this.x + d.x * this.speed * 2;
                let ny = this.y + d.y * this.speed * 2;
                return !isColliding(rectFromCenter(nx, ny, this.radius * 2 - 2), walls);
            });
            if (options.length) this.dir = options[Math.floor(Math.random() * options.length)];
        }

        draw() {
            if (this.img) {
                ctx.save();
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.clip();
                ctx.drawImage(this.img, this.x - this.radius, this.y - this.radius, this.radius * 2, this.radius * 2);
                ctx.restore();
            } else {
                ctx.fillStyle = "red";
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }

    // =================== Part 7: GRIALO Animation ===================
    function drawWinAnimation() {
        gameOverFrame++;
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;

        const scale = 1 + 0.3 * Math.sin(gameOverFrame * 0.1);
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.scale(scale, scale);

        const gradient = ctx.createLinearGradient(-150, 0, 150, 0);
        gradient.addColorStop(0, "yellow");
        gradient.addColorStop(0.5, "orange");
        gradient.addColorStop(1, "red");

        ctx.fillStyle = gradient;
        ctx.font = "bold 60px 'Courier New', monospace";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText("GRIALO!", 0, 0);
        ctx.restore();
    }

    // =================== Part 8: Main Game Loop ===================
    // =================== Part 8: Main Game Loop ===================
function initGame() {
    canvas = document.getElementById("gameCanvas");
    canvas.width = MAZE_MAP[0].length * TILE;
    canvas.height = MAZE_MAP.length * TILE;
    ctx = canvas.getContext("2d");

    const { playerPos, ghostPositions } = loadMaze();

    let playerImg = new Image();
    playerImg.src = "assets/player.png";
    let ghostImgs = [];
    for (let i = 1; i <= 3; i++) {
        let g = new Image();
        g.src = `assets/g${i}.png`;
        ghostImgs.push(g);
    }
    let coinImg = new Image();
    coinImg.src = "assets/rialo.png";

    player = new Player(playerPos.x, playerPos.y, playerImg);
    ghosts = ghostPositions.map((pos, idx) => new Ghost(pos.x, pos.y, ghostImgs[idx % ghostImgs.length]));

    document.addEventListener("keydown", (e) => {
        keys[e.key] = true;
        if (gameOver && e.key === "Enter") {
            score = 0;
            lives = LIVES;
            gameOver = false;
            win = false;
            keys = {};
            entryScreen(initGame);
        }
    });
    document.addEventListener("keyup", (e) => { keys[e.key] = false; });

    function gameLoop() {
        if (!gameOver) {
            player.update();
            ghosts.forEach(g => g.update());

            let playerRect = rectFromCenter(player.x, player.y, player.radius * 2 - 2);
            for (let i = pellets.length - 1; i >= 0; i--) {
                let pellet = pellets[i];
                if (
                    pellet.x - pelletRadius < playerRect.x + playerRect.width &&
                    pellet.x + pelletRadius > playerRect.x &&
                    pellet.y - pelletRadius < playerRect.y + playerRect.height &&
                    pellet.y + pelletRadius > playerRect.y
                ) {
                    pellets.splice(i, 1);
                    score += 10;
                }
            }

            ghosts.forEach(g => {
                if (
                    Math.abs(g.x - player.x) < TILE / 2 &&
                    Math.abs(g.y - player.y) < TILE / 2
                ) {
                    lives--;
                    if (lives > 0) {
                        player.x = playerPos.x;
                        player.y = playerPos.y;
                    } else {
                        gameOver = true;
                    }
                }
            });

            if (pellets.length === 0) {
                win = true;
                gameOver = true;
            }
        }

        ctx.fillStyle = "black";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        walls.forEach(w => {
            ctx.fillStyle = "blue";
            ctx.fillRect(w.x, w.y, w.width, w.height);
        });

        pellets.forEach(p => {
            ctx.drawImage(coinImg, p.x - TILE / 4, p.y - TILE / 4, TILE / 2, TILE / 2);
        });

        player.draw();
        ghosts.forEach(g => g.draw());

        ctx.fillStyle = "white";
        ctx.fillText("Score: " + score, 10, canvas.height - 10);
        ctx.fillText("Lives: " + lives, canvas.width - 80, canvas.height - 10);

        if (gameOver) {
            if (win) drawWinAnimation();
            else {
                ctx.fillStyle = "red";
                ctx.font = "30px Arial";
                ctx.fillText("GAME OVER Press Enter", canvas.width / 4, canvas.height / 2);
            }
        }

        requestAnimationFrame(gameLoop);
    }

    gameLoop();
}

window.onload = function () {
    canvas = document.getElementById("gameCanvas");
    canvas.width = MAZE_MAP[0].length * TILE;
    canvas.height = MAZE_MAP.length * TILE;
    ctx = canvas.getContext("2d");

    entryScreen(initGame);
};
