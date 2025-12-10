/**
 * Audio Visualizer Module
 * 실시간 오디오 시각화 (파형, 스펙트럼, 레벨 미터)
 */

class AudioVisualizer {
    constructor(canvas, options = {}) {
        this.canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;
        this.ctx = this.canvas.getContext('2d');

        this.options = {
            type: options.type || 'waveform', // 'waveform', 'spectrum', 'circle', 'bars'
            color: options.color || '#4A90A4',
            backgroundColor: options.backgroundColor || '#1a1a2e',
            lineWidth: options.lineWidth || 2,
            barWidth: options.barWidth || 3,
            barGap: options.barGap || 1,
            smoothing: options.smoothing || 0.8,
            mirror: options.mirror !== false,
            gradient: options.gradient !== false,
            responsive: options.responsive !== false,
            ...options
        };

        this.isRunning = false;
        this.animationId = null;
        this.dataSource = null;

        // Gradient colors
        this.gradientColors = options.gradientColors || [
            '#4A90A4', // Calm blue
            '#7ED6DF', // Light cyan
            '#A8E6CF', // Mint green
            '#FFD93D', // Warm yellow
            '#FF6B6B'  // Alert red
        ];

        // Initialize
        this.setupCanvas();
        if (this.options.responsive) {
            this.setupResizeHandler();
        }
    }

    setupCanvas() {
        // Set canvas size
        const rect = this.canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.ctx.scale(dpr, dpr);

        this.width = rect.width;
        this.height = rect.height;

        // Create gradient
        this.createGradient();
    }

    createGradient() {
        this.gradient = this.ctx.createLinearGradient(0, this.height, 0, 0);
        const step = 1 / (this.gradientColors.length - 1);
        this.gradientColors.forEach((color, index) => {
            this.gradient.addColorStop(index * step, color);
        });
    }

    setupResizeHandler() {
        const resizeObserver = new ResizeObserver(() => {
            this.setupCanvas();
        });
        resizeObserver.observe(this.canvas);
    }

    // =========================================================================
    // Data Source
    // =========================================================================

    setDataSource(source) {
        // source should have getFrequencyData() and getTimeDomainData() methods
        this.dataSource = source;
    }

    // =========================================================================
    // Visualization Types
    // =========================================================================

    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.draw();
    }

    stop() {
        this.isRunning = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        this.clear();
    }

    clear() {
        this.ctx.fillStyle = this.options.backgroundColor;
        this.ctx.fillRect(0, 0, this.width, this.height);
    }

    draw() {
        if (!this.isRunning) return;

        this.animationId = requestAnimationFrame(() => this.draw());

        // Clear canvas
        this.clear();

        if (!this.dataSource) {
            this.drawIdleState();
            return;
        }

        // Draw based on type
        switch (this.options.type) {
            case 'waveform':
                this.drawWaveform();
                break;
            case 'spectrum':
                this.drawSpectrum();
                break;
            case 'circle':
                this.drawCircle();
                break;
            case 'bars':
                this.drawBars();
                break;
            default:
                this.drawWaveform();
        }
    }

    drawIdleState() {
        // Draw a subtle idle animation
        const centerY = this.height / 2;
        this.ctx.strokeStyle = this.options.color;
        this.ctx.lineWidth = this.options.lineWidth;
        this.ctx.globalAlpha = 0.3;

        this.ctx.beginPath();
        this.ctx.moveTo(0, centerY);
        this.ctx.lineTo(this.width, centerY);
        this.ctx.stroke();

        this.ctx.globalAlpha = 1;
    }

    // =========================================================================
    // Waveform Visualization
    // =========================================================================

    drawWaveform() {
        const data = this.dataSource.getTimeDomainData();
        if (!data || data.length === 0) return;

        const sliceWidth = this.width / data.length;
        const centerY = this.height / 2;

        this.ctx.lineWidth = this.options.lineWidth;
        this.ctx.strokeStyle = this.options.gradient ? this.gradient : this.options.color;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';

        this.ctx.beginPath();

        let x = 0;
        for (let i = 0; i < data.length; i++) {
            const v = data[i] / 128.0; // Normalize to 0-2
            const y = v * centerY;

            if (i === 0) {
                this.ctx.moveTo(x, y);
            } else {
                this.ctx.lineTo(x, y);
            }

            x += sliceWidth;
        }

        this.ctx.stroke();

        // Draw mirror if enabled
        if (this.options.mirror) {
            this.ctx.globalAlpha = 0.3;
            this.ctx.beginPath();

            x = 0;
            for (let i = 0; i < data.length; i++) {
                const v = data[i] / 128.0;
                const y = this.height - (v * centerY);

                if (i === 0) {
                    this.ctx.moveTo(x, y);
                } else {
                    this.ctx.lineTo(x, y);
                }

                x += sliceWidth;
            }

            this.ctx.stroke();
            this.ctx.globalAlpha = 1;
        }
    }

    // =========================================================================
    // Spectrum (Frequency) Visualization
    // =========================================================================

    drawSpectrum() {
        const data = this.dataSource.getFrequencyData();
        if (!data || data.length === 0) return;

        const barCount = Math.min(64, data.length);
        const barWidth = this.width / barCount - this.options.barGap;

        this.ctx.fillStyle = this.options.gradient ? this.gradient : this.options.color;

        for (let i = 0; i < barCount; i++) {
            const dataIndex = Math.floor(i * data.length / barCount);
            const value = data[dataIndex] / 255;
            const barHeight = value * this.height;

            const x = i * (barWidth + this.options.barGap);
            const y = this.height - barHeight;

            // Round corners
            this.roundRect(x, y, barWidth, barHeight, 2);
        }

        // Draw mirror
        if (this.options.mirror) {
            this.ctx.globalAlpha = 0.3;
            for (let i = 0; i < barCount; i++) {
                const dataIndex = Math.floor(i * data.length / barCount);
                const value = data[dataIndex] / 255;
                const barHeight = value * this.height * 0.3;

                const x = i * (barWidth + this.options.barGap);

                this.roundRect(x, this.height, barWidth, barHeight, 2);
            }
            this.ctx.globalAlpha = 1;
        }
    }

    // =========================================================================
    // Circular Visualization
    // =========================================================================

    drawCircle() {
        const data = this.dataSource.getFrequencyData();
        if (!data || data.length === 0) return;

        const centerX = this.width / 2;
        const centerY = this.height / 2;
        const radius = Math.min(this.width, this.height) / 3;

        const barCount = 64;
        const angleStep = (Math.PI * 2) / barCount;

        this.ctx.strokeStyle = this.options.gradient ? this.gradient : this.options.color;
        this.ctx.lineWidth = this.options.barWidth;
        this.ctx.lineCap = 'round';

        for (let i = 0; i < barCount; i++) {
            const dataIndex = Math.floor(i * data.length / barCount);
            const value = data[dataIndex] / 255;
            const barHeight = value * radius;

            const angle = i * angleStep - Math.PI / 2;
            const x1 = centerX + Math.cos(angle) * radius;
            const y1 = centerY + Math.sin(angle) * radius;
            const x2 = centerX + Math.cos(angle) * (radius + barHeight);
            const y2 = centerY + Math.sin(angle) * (radius + barHeight);

            this.ctx.beginPath();
            this.ctx.moveTo(x1, y1);
            this.ctx.lineTo(x2, y2);
            this.ctx.stroke();
        }

        // Inner circle
        this.ctx.beginPath();
        this.ctx.arc(centerX, centerY, radius * 0.8, 0, Math.PI * 2);
        this.ctx.strokeStyle = this.options.color;
        this.ctx.globalAlpha = 0.2;
        this.ctx.stroke();
        this.ctx.globalAlpha = 1;
    }

    // =========================================================================
    // Bars Visualization
    // =========================================================================

    drawBars() {
        const data = this.dataSource.getFrequencyData();
        if (!data || data.length === 0) return;

        const barCount = 32;
        const barWidth = (this.width / barCount) - this.options.barGap;
        const centerY = this.height / 2;

        for (let i = 0; i < barCount; i++) {
            const dataIndex = Math.floor(i * data.length / barCount);
            const value = data[dataIndex] / 255;
            const barHeight = value * centerY;

            const x = i * (barWidth + this.options.barGap);

            // Create individual bar gradient
            const barGradient = this.ctx.createLinearGradient(x, centerY - barHeight, x, centerY + barHeight);
            barGradient.addColorStop(0, this.gradientColors[0]);
            barGradient.addColorStop(0.5, this.gradientColors[1]);
            barGradient.addColorStop(1, this.gradientColors[0]);

            this.ctx.fillStyle = barGradient;

            // Top bar
            this.roundRect(x, centerY - barHeight, barWidth, barHeight, 2);

            // Bottom bar (mirror)
            this.roundRect(x, centerY, barWidth, barHeight, 2);
        }
    }

    // =========================================================================
    // Utility Methods
    // =========================================================================

    roundRect(x, y, width, height, radius) {
        this.ctx.beginPath();
        this.ctx.moveTo(x + radius, y);
        this.ctx.lineTo(x + width - radius, y);
        this.ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        this.ctx.lineTo(x + width, y + height - radius);
        this.ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        this.ctx.lineTo(x + radius, y + height);
        this.ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        this.ctx.lineTo(x, y + radius);
        this.ctx.quadraticCurveTo(x, y, x + radius, y);
        this.ctx.closePath();
        this.ctx.fill();
    }

    setType(type) {
        this.options.type = type;
    }

    setColor(color) {
        this.options.color = color;
    }

    setGradientColors(colors) {
        this.gradientColors = colors;
        this.createGradient();
    }
}

// ============================================================================
// Level Meter Component
// ============================================================================

class LevelMeter {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.getElementById(container)
            : container;

        this.options = {
            width: options.width || 10,
            height: options.height || 100,
            segments: options.segments || 20,
            smoothing: options.smoothing || 0.7,
            colors: options.colors || {
                low: '#4A90A4',
                medium: '#FFD93D',
                high: '#FF6B6B'
            },
            thresholds: options.thresholds || {
                medium: 0.5,
                high: 0.8
            },
            ...options
        };

        this.currentLevel = 0;
        this.peakLevel = 0;
        this.peakHoldTime = 0;
        this.peakHoldDuration = 1000; // ms

        this.createElement();
    }

    createElement() {
        this.element = document.createElement('div');
        this.element.className = 'level-meter';
        this.element.style.cssText = `
            width: ${this.options.width}px;
            height: ${this.options.height}px;
            background: #1a1a2e;
            border-radius: 5px;
            display: flex;
            flex-direction: column-reverse;
            overflow: hidden;
            gap: 1px;
            padding: 2px;
        `;

        // Create segments
        this.segments = [];
        const segmentHeight = (this.options.height - 4) / this.options.segments - 1;

        for (let i = 0; i < this.options.segments; i++) {
            const segment = document.createElement('div');
            segment.style.cssText = `
                width: 100%;
                height: ${segmentHeight}px;
                background: #2d2d44;
                border-radius: 2px;
                transition: background-color 0.05s;
            `;
            this.element.appendChild(segment);
            this.segments.push(segment);
        }

        // Peak indicator
        this.peakIndicator = document.createElement('div');
        this.peakIndicator.style.cssText = `
            position: absolute;
            width: 100%;
            height: 2px;
            background: white;
            left: 0;
            transition: bottom 0.1s;
        `;
        this.element.style.position = 'relative';
        this.element.appendChild(this.peakIndicator);

        this.container.appendChild(this.element);
    }

    update(level) {
        // Smooth the level
        this.currentLevel = this.currentLevel * this.options.smoothing +
            level * (1 - this.options.smoothing);

        // Update peak
        if (this.currentLevel > this.peakLevel) {
            this.peakLevel = this.currentLevel;
            this.peakHoldTime = Date.now();
        } else if (Date.now() - this.peakHoldTime > this.peakHoldDuration) {
            this.peakLevel *= 0.95;
        }

        // Update segments
        const activeSegments = Math.floor(this.currentLevel * this.options.segments);

        this.segments.forEach((segment, index) => {
            const segmentRatio = index / this.options.segments;

            if (index < activeSegments) {
                if (segmentRatio >= this.options.thresholds.high) {
                    segment.style.backgroundColor = this.options.colors.high;
                } else if (segmentRatio >= this.options.thresholds.medium) {
                    segment.style.backgroundColor = this.options.colors.medium;
                } else {
                    segment.style.backgroundColor = this.options.colors.low;
                }
            } else {
                segment.style.backgroundColor = '#2d2d44';
            }
        });

        // Update peak indicator
        const peakPosition = this.peakLevel * (this.options.height - 4);
        this.peakIndicator.style.bottom = `${peakPosition}px`;
    }

    reset() {
        this.currentLevel = 0;
        this.peakLevel = 0;
        this.segments.forEach(segment => {
            segment.style.backgroundColor = '#2d2d44';
        });
        this.peakIndicator.style.bottom = '0px';
    }

    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

// ============================================================================
// Recording Animation
// ============================================================================

class RecordingIndicator {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.getElementById(container)
            : container;

        this.options = {
            size: options.size || 60,
            color: options.color || '#FF6B6B',
            pulseColor: options.pulseColor || 'rgba(255, 107, 107, 0.3)',
            ...options
        };

        this.isRecording = false;
        this.createElement();
    }

    createElement() {
        this.element = document.createElement('div');
        this.element.className = 'recording-indicator';
        this.element.innerHTML = `
            <div class="recording-pulse"></div>
            <div class="recording-dot"></div>
        `;
        this.element.style.cssText = `
            width: ${this.options.size}px;
            height: ${this.options.size}px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .recording-indicator .recording-pulse {
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: ${this.options.pulseColor};
                opacity: 0;
                transform: scale(0.8);
            }

            .recording-indicator.active .recording-pulse {
                animation: pulse 1.5s ease-out infinite;
            }

            .recording-indicator .recording-dot {
                width: 40%;
                height: 40%;
                border-radius: 50%;
                background: ${this.options.color};
                opacity: 0.5;
                transition: all 0.3s ease;
            }

            .recording-indicator.active .recording-dot {
                opacity: 1;
                animation: blink 1s ease-in-out infinite;
            }

            @keyframes pulse {
                0% {
                    transform: scale(0.8);
                    opacity: 0.8;
                }
                100% {
                    transform: scale(1.5);
                    opacity: 0;
                }
            }

            @keyframes blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
        `;
        document.head.appendChild(style);

        this.container.appendChild(this.element);
    }

    start() {
        this.isRecording = true;
        this.element.classList.add('active');
    }

    stop() {
        this.isRecording = false;
        this.element.classList.remove('active');
    }

    toggle() {
        if (this.isRecording) {
            this.stop();
        } else {
            this.start();
        }
    }

    destroy() {
        if (this.element && this.element.parentNode) {
            this.element.parentNode.removeChild(this.element);
        }
    }
}

// Export
window.AudioVisualizer = AudioVisualizer;
window.LevelMeter = LevelMeter;
window.RecordingIndicator = RecordingIndicator;
