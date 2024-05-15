const ballsContainer = document.getElementById("balls-container");

function getRandomArbitrary(min, max) {
    return Math.random() * (max - min) + min;
}

function getRandomArbitraryInt(min, max) {
    return Math.round(getRandomArbitrary(min, max));
}

function weightedRandom(max, numDice) {
    let num = 0;
    for (let i = 0; i < numDice; i++) {
        num += Math.random() * (max/numDice);
    }    
    return num;
}

function getRandomArbitraryCentered(min, max) {
    return weightedRandom(max-min, 5) + min;
}

function createBall(x, y, h, s, l, size) {
    var elem = document.createElementNS("http://www.w3.org/2000/svg", "ellipse");
    elem.setAttribute("rx", size);
    elem.setAttribute("ry", size);
    elem.setAttribute("cx", x);
    elem.setAttribute("cy", y);
    elem.setAttribute("fill", "hsl("+ h + ", " + s + "%, " + l + "%)");

    ballsContainer.appendChild(elem);

    animateBall(elem, x, y, size, 0);
}

function animateBall(ball, x, y, size, lastMs) {
    var animMs = getRandomArbitraryInt(1000, 2500);

    var x2 = getRandomArbitraryCentered(size, 800-size);
    var y2 = getRandomArbitraryCentered(size, 800-size);

    var left = x2-x;
    var top = y2-y;

    ball.setAttribute("style", "transition: transform "+ animMs +"ms ease; transform: translate("+ left + "px, " + top + "px);")

    setTimeout(() => {
        animateBall(ball, x, y, size, animMs);
    }, lastMs);
}

function createBalls() {
    var ballCount = getRandomArbitrary(10, 15)
    for (i = 0; i < ballCount; i++) {
        var size = getRandomArbitraryInt(50, 100);
        var x = getRandomArbitraryCentered(size, 800-size);
        var y = getRandomArbitraryCentered(size, 800-size);
        var h = getRandomArbitraryInt(90, 150);
        var s = getRandomArbitraryInt(80, 100);
        var l = getRandomArbitraryInt(40, 60);
        createBall(x, y, h, s, l, size);
    }
}

createBalls()