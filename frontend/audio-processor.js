/**
 * Audio Processor Module
 * 프론트엔드 오디오 품질 개선
 *
 * 기능:
 * - 노이즈 게이트
 * - 컴프레서
 * - 에코 캔슬링 (Web Audio API)
 * - 자동 이득 제어
 */

class AudioQualityProcessor {
    constructor(audioContext, options = {}) {
        this.audioContext = audioContext;
        this.options = {
            enableNoiseGate: options.enableNoiseGate !== false,
            enableCompressor: options.enableCompressor !== false,
            enableAGC: options.enableAGC !== false,
            noiseGateThreshold: options.noiseGateThreshold || -50, // dB
            compressorThreshold: options.compressorThreshold || -24,
            compressorRatio: options.compressorRatio || 4,
            targetLevel: options.targetLevel || -20, // dB
            ...options
        };

        this.nodes = {};
        this.isInitialized = false;
    }

    /**
     * 프로세서 체인 초기화
     */
    initialize() {
        if (this.isInitialized) return;

        // 입력 게인 (AGC용)
        this.nodes.inputGain = this.audioContext.createGain();
        this.nodes.inputGain.gain.value = 1.0;

        // 하이패스 필터 (저주파 노이즈 제거)
        this.nodes.highpass = this.audioContext.createBiquadFilter();
        this.nodes.highpass.type = 'highpass';
        this.nodes.highpass.frequency.value = 80;
        this.nodes.highpass.Q.value = 0.7;

        // 로우패스 필터 (고주파 노이즈 제거)
        this.nodes.lowpass = this.audioContext.createBiquadFilter();
        this.nodes.lowpass.type = 'lowpass';
        this.nodes.lowpass.frequency.value = 8000;
        this.nodes.lowpass.Q.value = 0.7;

        // 노이즈 게이트
        if (this.options.enableNoiseGate) {
            this.nodes.noiseGate = new NoiseGate(this.audioContext, {
                threshold: this.options.noiseGateThreshold,
                attack: 0.005,
                release: 0.05
            });
        }

        // 컴프레서
        if (this.options.enableCompressor) {
            this.nodes.compressor = this.audioContext.createDynamicsCompressor();
            this.nodes.compressor.threshold.value = this.options.compressorThreshold;
            this.nodes.compressor.knee.value = 10;
            this.nodes.compressor.ratio.value = this.options.compressorRatio;
            this.nodes.compressor.attack.value = 0.003;
            this.nodes.compressor.release.value = 0.25;
        }

        // 출력 게인
        this.nodes.outputGain = this.audioContext.createGain();
        this.nodes.outputGain.gain.value = 1.0;

        // 레벨 분석기 (AGC용)
        this.nodes.analyser = this.audioContext.createAnalyser();
        this.nodes.analyser.fftSize = 256;
        this.nodes.analyser.smoothingTimeConstant = 0.8;

        this.isInitialized = true;
    }

    /**
     * 프로세서 체인 연결
     * @param {AudioNode} source - 입력 노드
     * @param {AudioNode} destination - 출력 노드
     */
    connect(source, destination) {
        if (!this.isInitialized) {
            this.initialize();
        }

        // 체인 연결: source → inputGain → highpass → lowpass → [noiseGate] → [compressor] → outputGain → analyser → destination
        let currentNode = source;

        currentNode.connect(this.nodes.inputGain);
        currentNode = this.nodes.inputGain;

        currentNode.connect(this.nodes.highpass);
        currentNode = this.nodes.highpass;

        currentNode.connect(this.nodes.lowpass);
        currentNode = this.nodes.lowpass;

        if (this.nodes.noiseGate) {
            currentNode.connect(this.nodes.noiseGate.input);
            currentNode = this.nodes.noiseGate.output;
        }

        if (this.nodes.compressor) {
            currentNode.connect(this.nodes.compressor);
            currentNode = this.nodes.compressor;
        }

        currentNode.connect(this.nodes.outputGain);
        this.nodes.outputGain.connect(this.nodes.analyser);
        this.nodes.analyser.connect(destination);

        // AGC 시작
        if (this.options.enableAGC) {
            this.startAGC();
        }
    }

    /**
     * 자동 이득 제어 시작
     */
    startAGC() {
        const dataArray = new Float32Array(this.nodes.analyser.frequencyBinCount);

        const adjustGain = () => {
            if (!this.isInitialized) return;

            this.nodes.analyser.getFloatTimeDomainData(dataArray);

            // RMS 레벨 계산
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i] * dataArray[i];
            }
            const rms = Math.sqrt(sum / dataArray.length);
            const dbLevel = 20 * Math.log10(Math.max(rms, 1e-10));

            // 목표 레벨과 비교
            const targetDb = this.options.targetLevel;
            const diff = targetDb - dbLevel;

            // 이득 조절 (부드럽게)
            if (Math.abs(diff) > 3) { // 3dB 이상 차이날 때만
                const gainChange = Math.pow(10, diff / 40); // 절반만 보정
                const currentGain = this.nodes.inputGain.gain.value;
                const newGain = Math.max(0.1, Math.min(10, currentGain * gainChange));

                this.nodes.inputGain.gain.setTargetAtTime(
                    newGain,
                    this.audioContext.currentTime,
                    0.1
                );
            }

            requestAnimationFrame(adjustGain);
        };

        adjustGain();
    }

    /**
     * 이득 설정
     */
    setInputGain(value) {
        if (this.nodes.inputGain) {
            this.nodes.inputGain.gain.setTargetAtTime(
                value,
                this.audioContext.currentTime,
                0.01
            );
        }
    }

    setOutputGain(value) {
        if (this.nodes.outputGain) {
            this.nodes.outputGain.gain.setTargetAtTime(
                value,
                this.audioContext.currentTime,
                0.01
            );
        }
    }

    /**
     * 현재 레벨 가져오기
     */
    getLevel() {
        if (!this.nodes.analyser) return 0;

        const dataArray = new Float32Array(this.nodes.analyser.frequencyBinCount);
        this.nodes.analyser.getFloatTimeDomainData(dataArray);

        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i] * dataArray[i];
        }
        return Math.sqrt(sum / dataArray.length);
    }

    /**
     * 정리
     */
    destroy() {
        this.isInitialized = false;
        Object.values(this.nodes).forEach(node => {
            if (node && node.disconnect) {
                try {
                    node.disconnect();
                } catch (e) {}
            }
        });
        this.nodes = {};
    }
}


/**
 * 노이즈 게이트
 * 특정 임계값 이하 신호 억제
 */
class NoiseGate {
    constructor(audioContext, options = {}) {
        this.audioContext = audioContext;
        this.threshold = options.threshold || -50; // dB
        this.attack = options.attack || 0.005; // seconds
        this.release = options.release || 0.05; // seconds

        // 노드 생성
        this.input = audioContext.createGain();
        this.output = audioContext.createGain();
        this.analyser = audioContext.createAnalyser();
        this.analyser.fftSize = 256;

        // 연결
        this.input.connect(this.analyser);
        this.input.connect(this.output);

        // 게이트 제어 시작
        this.isOpen = true;
        this.startGating();
    }

    startGating() {
        const dataArray = new Float32Array(this.analyser.frequencyBinCount);

        const checkLevel = () => {
            this.analyser.getFloatTimeDomainData(dataArray);

            // RMS 계산
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i] * dataArray[i];
            }
            const rms = Math.sqrt(sum / dataArray.length);
            const dbLevel = 20 * Math.log10(Math.max(rms, 1e-10));

            // 게이트 열기/닫기
            if (dbLevel > this.threshold) {
                if (!this.isOpen) {
                    this.output.gain.setTargetAtTime(1.0, this.audioContext.currentTime, this.attack);
                    this.isOpen = true;
                }
            } else {
                if (this.isOpen) {
                    this.output.gain.setTargetAtTime(0.0, this.audioContext.currentTime, this.release);
                    this.isOpen = false;
                }
            }

            requestAnimationFrame(checkLevel);
        };

        checkLevel();
    }
}


/**
 * 에코 캔슬러 (클라이언트 측)
 * 재생 중인 오디오와 마이크 입력 간 에코 감소
 */
class ClientEchoCanceller {
    constructor(audioContext, options = {}) {
        this.audioContext = audioContext;
        this.filterLength = options.filterLength || 512;
        this.mu = options.learningRate || 0.1;

        // 적응 필터 계수
        this.filterCoeffs = new Float32Array(this.filterLength);

        // 참조 신호 버퍼
        this.refBuffer = new Float32Array(this.filterLength);

        // AudioWorklet 사용 (지원 시)
        this.workletNode = null;
    }

    async initialize() {
        if (this.audioContext.audioWorklet) {
            try {
                const processorCode = `
                    class EchoCancellerProcessor extends AudioWorkletProcessor {
                        constructor() {
                            super();
                            this.filterLength = 512;
                            this.filterCoeffs = new Float32Array(this.filterLength);
                            this.refBuffer = new Float32Array(this.filterLength);
                            this.mu = 0.1;
                            this.delta = 1e-6;

                            this.port.onmessage = (e) => {
                                if (e.data.type === 'reference') {
                                    this.updateReference(e.data.audio);
                                }
                            };
                        }

                        updateReference(audio) {
                            const newRef = new Float32Array(audio);
                            this.refBuffer.set(this.refBuffer.subarray(newRef.length));
                            this.refBuffer.set(newRef, this.filterLength - newRef.length);
                        }

                        process(inputs, outputs, parameters) {
                            const input = inputs[0];
                            const output = outputs[0];

                            if (input.length > 0 && output.length > 0) {
                                const inputChannel = input[0];
                                const outputChannel = output[0];

                                for (let i = 0; i < inputChannel.length; i++) {
                                    // 에코 추정
                                    let echoEstimate = 0;
                                    for (let j = 0; j < this.filterLength; j++) {
                                        echoEstimate += this.filterCoeffs[j] * this.refBuffer[j];
                                    }

                                    // 에코 제거
                                    const error = inputChannel[i] - echoEstimate;
                                    outputChannel[i] = error;

                                    // NLMS 업데이트
                                    let norm = this.delta;
                                    for (let j = 0; j < this.filterLength; j++) {
                                        norm += this.refBuffer[j] * this.refBuffer[j];
                                    }

                                    for (let j = 0; j < this.filterLength; j++) {
                                        this.filterCoeffs[j] += (this.mu / norm) * error * this.refBuffer[j];
                                    }
                                }
                            }

                            return true;
                        }
                    }
                    registerProcessor('echo-canceller', EchoCancellerProcessor);
                `;

                const blob = new Blob([processorCode], { type: 'application/javascript' });
                const url = URL.createObjectURL(blob);

                await this.audioContext.audioWorklet.addModule(url);
                this.workletNode = new AudioWorkletNode(this.audioContext, 'echo-canceller');

                URL.revokeObjectURL(url);
                return true;

            } catch (e) {
                console.warn('AudioWorklet not available for AEC:', e);
                return false;
            }
        }
        return false;
    }

    setReference(playbackAudio) {
        if (this.workletNode) {
            this.workletNode.port.postMessage({
                type: 'reference',
                audio: Array.from(playbackAudio)
            });
        }
    }

    get input() {
        return this.workletNode || this.audioContext.createGain();
    }

    get output() {
        return this.workletNode || this.audioContext.createGain();
    }
}


/**
 * 지터 버퍼
 * 네트워크 지연 변동 흡수
 */
class ClientJitterBuffer {
    constructor(options = {}) {
        this.targetDelayMs = options.targetDelayMs || 60;
        this.minDelayMs = options.minDelayMs || 20;
        this.maxDelayMs = options.maxDelayMs || 200;

        this.buffer = [];
        this.totalDuration = 0;
        this.isPlaying = false;

        // 적응형 조절
        this.delayHistory = [];
        this.maxHistory = 50;
    }

    push(audioData, duration) {
        this.buffer.push({ data: audioData, duration: duration });
        this.totalDuration += duration;

        // 오버플로우 방지
        while (this.totalDuration > this.maxDelayMs) {
            const removed = this.buffer.shift();
            this.totalDuration -= removed.duration;
            console.warn('Jitter buffer overflow');
        }
    }

    pop() {
        // 최소 버퍼 확인
        if (!this.isPlaying && this.totalDuration < this.minDelayMs) {
            return null;
        }

        this.isPlaying = true;

        if (this.buffer.length === 0) {
            this.isPlaying = false;
            return null;
        }

        const item = this.buffer.shift();
        this.totalDuration -= item.duration;

        return item.data;
    }

    clear() {
        this.buffer = [];
        this.totalDuration = 0;
        this.isPlaying = false;
    }

    get bufferedMs() {
        return this.totalDuration;
    }
}


// Export
window.AudioQualityProcessor = AudioQualityProcessor;
window.NoiseGate = NoiseGate;
window.ClientEchoCanceller = ClientEchoCanceller;
window.ClientJitterBuffer = ClientJitterBuffer;
