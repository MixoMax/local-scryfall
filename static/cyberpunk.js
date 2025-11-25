// Cyberpunk Design System - Interactive Logic

document.addEventListener('DOMContentLoaded', () => {
    initCursor();
    // Defer heavy visuals slightly to ensure DOM is ready
    setTimeout(() => {
        initBackground();
        initSmoothScroll();
        initAnimations();
    }, 100);
});

// 1. Custom Cursor Logic
function initCursor() {
    // Remove default cursor from body
    document.body.style.cursor = 'none';

    const cursor = document.createElement('div');
    cursor.id = 'cursor';
    document.body.appendChild(cursor);

    // Initial position off-screen
    let mouseX = -100;
    let mouseY = -100;

    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        cursor.style.left = mouseX + 'px';
        cursor.style.top = mouseY + 'px';
    });

    // Add hover effect listeners
    const addHoverListeners = () => {
        const hoverTargets = document.querySelectorAll('a, button, .hover-trigger, input, select, .card-item, label');
        hoverTargets.forEach(el => {
            el.style.cursor = 'none'; // Force no cursor on elements
            
            el.addEventListener('mouseenter', () => cursor.classList.add('hovered'));
            el.addEventListener('mouseleave', () => cursor.classList.remove('hovered'));
        });
    };

    addHoverListeners();
    
    // Re-apply listeners when DOM changes (for dynamic content like search results)
    const observer = new MutationObserver(addHoverListeners);
    observer.observe(document.body, { childList: true, subtree: true });
}

// 2. Three.js Background (Deep Sea / Network)
function initBackground() {
    const canvasContainer = document.createElement('div');
    canvasContainer.id = 'bg-canvas';
    // Insert as first child of body
    document.body.insertBefore(canvasContainer, document.body.firstChild);

    // Check if Three.js is loaded
    if (typeof THREE === 'undefined') {
        console.warn('Three.js not loaded');
        return;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Performance optimization
    canvasContainer.appendChild(renderer.domElement);

    // Particles - "Data Dust"
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 800;
    const posArray = new Float32Array(particlesCount * 3);

    for(let i = 0; i < particlesCount * 3; i++) {
        posArray[i] = (Math.random() - 0.5) * 20; // Spread
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));

    // Cyan particles
    const material = new THREE.PointsMaterial({
        size: 0.02,
        color: 0x00f3ff,
        transparent: true,
        opacity: 0.3, // Reduced opacity
    });

    const particlesMesh = new THREE.Points(particlesGeometry, material);
    scene.add(particlesMesh);

    // Wireframe Grid - "The Net"
    // Made larger, fewer divisions, darker, and pushed further down
    const gridHelper = new THREE.GridHelper(80, 40, 0x1a1a1a, 0x050505);
    gridHelper.position.y = -8;
    gridHelper.rotation.x = 0.1; // Reduced tilt
    scene.add(gridHelper);

    camera.position.z = 3;

    // Mouse interaction for parallax
    let mouseX = 0;
    let mouseY = 0;
    let targetX = 0;
    let targetY = 0;

    const windowHalfX = window.innerWidth / 2;
    const windowHalfY = window.innerHeight / 2;

    document.addEventListener('mousemove', (event) => {
        mouseX = (event.clientX - windowHalfX);
        mouseY = (event.clientY - windowHalfY);
    });

    const clock = new THREE.Clock();

    function animate() {
        requestAnimationFrame(animate);
        const elapsedTime = clock.getElapsedTime();

        targetX = mouseX * 0.0005; // Reduced mouse sensitivity
        targetY = mouseY * 0.0005;

        // Smooth rotation - Slowed down significantly
        particlesMesh.rotation.y += 0.0002;
        particlesMesh.rotation.x += 0.0001;

        // Parallax effect - Smoother/Slower
        particlesMesh.rotation.y += 0.02 * (targetX - particlesMesh.rotation.y);
        particlesMesh.rotation.x += 0.02 * (targetY - particlesMesh.rotation.x);

        // Gentle floating - Reduced amplitude and speed
        particlesMesh.position.y = Math.sin(elapsedTime * 0.1) * 0.1;

        renderer.render(scene, camera);
    }

    animate();

    // Handle Resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

// 3. Smooth Scroll (Lenis)
function initSmoothScroll() {
    if (typeof Lenis === 'undefined') return;

    const lenis = new Lenis({
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        direction: 'vertical',
        gestureDirection: 'vertical',
        smooth: true,
        mouseMultiplier: 1,
        smoothTouch: false,
        touchMultiplier: 2,
    });

    function raf(time) {
        lenis.raf(time);
        requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);
}

// 4. GSAP Animations
function initAnimations() {
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;

    gsap.registerPlugin(ScrollTrigger);

    // Animate sections on scroll
    const sections = document.querySelectorAll('section, .card-item, .glass-panel, .terminal-box, header, .stats-container');
    
    sections.forEach(section => {
        gsap.fromTo(section, 
            { 
                y: 50, 
                opacity: 0 
            },
            {
                y: 0,
                opacity: 1,
                duration: 0.8,
                ease: "power3.out",
                scrollTrigger: {
                    trigger: section,
                    start: "top 85%", // Start animation when top of element hits 85% of viewport height
                    toggleActions: "play none none reverse"
                }
            }
        );
    });
}