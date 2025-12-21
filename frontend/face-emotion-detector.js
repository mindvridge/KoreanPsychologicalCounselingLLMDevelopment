/**
 * Face Emotion Detector
 * 웹캠을 통한 얼굴 인식 및 감정 분석
 */

class FaceEmotionDetector {
    constructor(options = {}) {
        this.options = {
            videoElement: options.videoElement || null,
            canvasElement: options.canvasElement || null,
            emotionDisplayElement: options.emotionDisplayElement || null,
            detectionInterval: options.detectionInterval || 100, // ms
            minConfidence: options.minConfidence || 0.3, // 신뢰도 임계값 낮춤
            minFaceSize: options.minFaceSize || 50, // 최소 얼굴 크기 (픽셀)
            ...options
        };

        this.isDetecting = false;
        this.stream = null;
        this.detectionInterval = null;
        this.modelsLoaded = false;
        
        // 감정 매핑 (face-api.js 감정 → 한국어)
        this.emotionMap = {
            'happy': { emoji: '😊', label: '기쁨', color: '#FFD93D' },
            'sad': { emoji: '😢', label: '슬픔', color: '#74B9FF' },
            'angry': { emoji: '😠', label: '분노', color: '#FF7675' },
            'fearful': { emoji: '😨', label: '두려움', color: '#A29BFE' },
            'disgusted': { emoji: '🤢', label: '혐오', color: '#6C5CE7' },
            'surprised': { emoji: '😲', label: '놀람', color: '#FDCB6E' },
            'neutral': { emoji: '😐', label: '중립', color: '#B2BEC3' }
        };

        // 현재 감정 상태
        this.currentEmotion = null;
        this.lastValidEmotion = null; // 마지막으로 유효하게 인식된 감정
        this.emotionHistory = [];
        this.recentDetections = []; // 최근 감지 결과들 (평균화용)
        this.maxRecentDetections = 5; // 평균화에 사용할 최근 감지 개수
        this.onEmotionDetected = options.onEmotionDetected || null;
    }

    /**
     * face-api.js 모델 로드
     */
    async loadModels() {
        if (this.modelsLoaded) {
            return true;
        }

        try {
            console.log('Loading face-api.js models...');
            
            // 모델 경로 설정 (올바른 GitHub 경로 사용)
            // face-api.js 공식 저장소의 weights 폴더 사용
            const MODEL_URL = 'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights';
            
            // 모델 로드 (필요한 모델만 로드)
            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
                faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
                faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL)
            ]);

            this.modelsLoaded = true;
            console.log('Face-api.js models loaded successfully');
            return true;
        } catch (error) {
            console.error('Error loading face-api.js models:', error);
            console.warn('Face detection will be limited without models');
            // 모델 로드 실패해도 계속 진행 (기능 제한)
            return false;
        }
    }

    /**
     * 웹캠 시작
     */
    async startCamera() {
        try {
            // 모델 로드 확인
            if (!this.modelsLoaded) {
                console.log('Loading face detection models...');
                const loaded = await this.loadModels();
                if (!loaded) {
                    console.error('Failed to load face detection models');
                    throw new Error('Failed to load face detection models');
                }
                console.log('Face detection models loaded successfully');
            }

            // 웹캠 접근
            console.log('Requesting camera access...');
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            });

            if (this.options.videoElement) {
                this.options.videoElement.srcObject = this.stream;
                await this.options.videoElement.play();
                console.log('Camera video started');
            }

            // 비디오가 준비될 때까지 대기
            await new Promise((resolve) => {
                if (this.options.videoElement.readyState >= 2) {
                    resolve();
                } else {
                    this.options.videoElement.addEventListener('loadedmetadata', resolve, { once: true });
                }
            });

            // 감지 시작
            console.log('Starting emotion detection...');
            this.startDetection();
            
            return true;
        } catch (error) {
            console.error('Error starting camera:', error);
            // UI에 오류 표시
            if (this.options.emotionDisplayElement) {
                this.updateEmotionDisplay(null);
            }
            throw error;
        }
    }

    /**
     * 웹캠 중지
     */
    stopCamera() {
        this.stopDetection();

        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }

        if (this.options.videoElement) {
            this.options.videoElement.srcObject = null;
        }

        // UI 초기화
        this.updateEmotionDisplay(null);
    }

    /**
     * 얼굴 감지 및 감정 분석 시작
     */
    startDetection() {
        if (this.isDetecting) {
            return;
        }

        this.isDetecting = true;
        const video = this.options.videoElement;
        const canvas = this.options.canvasElement;

        if (!video || !canvas) {
            console.error('Video or canvas element not found');
            return;
        }

        // Canvas 크기 설정
        const updateCanvasSize = () => {
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
        };
        updateCanvasSize();
        video.addEventListener('loadedmetadata', updateCanvasSize);

        // 주기적으로 감지 수행
        this.detectionInterval = setInterval(async () => {
            if (!this.isDetecting) {
                return;
            }
            
            // 비디오가 준비되지 않았으면 대기
            if (video.readyState < video.HAVE_METADATA) {
                return;
            }

            try {
                await this.detectEmotion();
            } catch (error) {
                console.error('Error detecting emotion:', error);
                // 오류 발생 시에도 UI 업데이트 (얼굴 인식 불가 메시지)
                if (error.message && error.message.includes('face')) {
                    this.updateEmotionDisplay(null);
                }
            }
        }, this.options.detectionInterval);
    }

    /**
     * 감지 중지
     */
    stopDetection() {
        this.isDetecting = false;
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
            this.detectionInterval = null;
        }
    }

    /**
     * 얼굴 감지 및 감정 분석
     */
    async detectEmotion() {
        const video = this.options.videoElement;
        const canvas = this.options.canvasElement;

        if (!video || !canvas || !this.modelsLoaded) {
            console.warn('Cannot detect emotion: missing video, canvas, or models not loaded');
            return;
        }

        // 비디오가 준비되지 않았으면 대기
        if (video.readyState < video.HAVE_METADATA) {
            return;
        }

        try {
            // Canvas 크기 업데이트 (비디오 크기에 맞춤)
            if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
                canvas.width = video.videoWidth || 640;
                canvas.height = video.videoHeight || 480;
            }

            // Canvas에 비디오 프레임 그리기
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            // 얼굴 감지 및 감정 분석 (개선된 옵션 사용)
            // inputSize를 크게 하면 더 정확하지만 느려짐, scoreThreshold를 낮추면 더 많은 얼굴 감지
            const detections = await faceapi
                .detectAllFaces(video, new faceapi.TinyFaceDetectorOptions({
                    inputSize: 512, // 기본값 416보다 크게 설정 (더 정확한 감지)
                    scoreThreshold: 0.3 // 기본값 0.5보다 낮게 설정 (더 많은 얼굴 감지)
                }))
                .withFaceLandmarks()
                .withFaceExpressions();

            if (detections.length === 0) {
                // 얼굴이 감지되지 않음 - 이전 상태 유지
                if (this.lastValidEmotion) {
                    this.updateEmotionDisplay(this.lastValidEmotion, true); // isPreviousState = true
                } else {
                    this.updateEmotionDisplay(null);
                }
                return;
            }

            // 가장 큰 얼굴 선택 (가장 가까운 얼굴)
            const detection = detections.reduce((prev, current) => {
                const prevSize = prev.detection.box.width * prev.detection.box.height;
                const currentSize = current.detection.box.width * current.detection.box.height;
                return currentSize > prevSize ? current : prev;
            });

            // 얼굴 크기 필터링 (너무 작은 얼굴 제외)
            const faceSize = Math.min(detection.detection.box.width, detection.detection.box.height);
            if (faceSize < this.options.minFaceSize) {
                // 얼굴이 너무 작음 - 이전 상태 유지
                if (this.lastValidEmotion) {
                    this.updateEmotionDisplay(this.lastValidEmotion, true);
                } else {
                    this.updateEmotionDisplay(null);
                }
                return;
            }

            // 감정 추출
            if (!detection.expressions) {
                // 감정 데이터 없음 - 이전 상태 유지
                if (this.lastValidEmotion) {
                    this.updateEmotionDisplay(this.lastValidEmotion, true);
                } else {
                    this.updateEmotionDisplay(null);
                }
                return;
            }

            const expressions = detection.expressions;
            const emotions = Object.entries(expressions)
                .map(([emotion, score]) => ({ emotion, score }))
                .sort((a, b) => b.score - a.score);

            const topEmotion = emotions[0];
            
            // 신뢰도가 최소값 이상인 경우만 처리
            if (topEmotion && topEmotion.score >= this.options.minConfidence) {
                // 최근 감지 결과에 추가 (평균화용)
                this.recentDetections.push({
                    emotion: topEmotion.emotion,
                    confidence: topEmotion.score,
                    allEmotions: expressions,
                    timestamp: Date.now()
                });

                // 최근 감지 결과 개수 제한
                if (this.recentDetections.length > this.maxRecentDetections) {
                    this.recentDetections.shift();
                }

                // 최근 감지 결과들의 평균 계산 (더 안정적인 감정 인식)
                const averagedEmotion = this.calculateAveragedEmotion();

                if (averagedEmotion) {
                    this.currentEmotion = averagedEmotion;
                    this.lastValidEmotion = averagedEmotion; // 유효한 감정으로 저장

                    // 감정 히스토리에 추가
                    this.emotionHistory.push({
                        ...this.currentEmotion,
                        timestamp: new Date().toISOString()
                    });

                    // 최근 10개만 유지
                    if (this.emotionHistory.length > 10) {
                        this.emotionHistory.shift();
                    }

                    // UI 업데이트
                    this.updateEmotionDisplay(this.currentEmotion, false);

                    // 콜백 호출
                    if (this.onEmotionDetected) {
                        this.onEmotionDetected(this.currentEmotion);
                    }
                }
            } else {
                // 신뢰도가 낮음 - 이전 상태 유지
                if (this.lastValidEmotion) {
                    this.updateEmotionDisplay(this.lastValidEmotion, true);
                } else {
                    this.updateEmotionDisplay(null);
                }
            }
        } catch (error) {
            console.error('Error in detectEmotion:', error);
            // 오류 발생 시에도 UI 업데이트
            this.updateEmotionDisplay(null);
        }
    }

    /**
     * 최근 감지 결과들의 평균 계산
     */
    calculateAveragedEmotion() {
        if (this.recentDetections.length === 0) {
            return null;
        }

        // 모든 감정의 평균 점수 계산
        const emotionScores = {};
        this.recentDetections.forEach(detection => {
            Object.entries(detection.allEmotions).forEach(([emotion, score]) => {
                if (!emotionScores[emotion]) {
                    emotionScores[emotion] = [];
                }
                emotionScores[emotion].push(score);
            });
        });

        // 평균 계산
        const averagedScores = {};
        Object.entries(emotionScores).forEach(([emotion, scores]) => {
            const sum = scores.reduce((a, b) => a + b, 0);
            averagedScores[emotion] = sum / scores.length;
        });

        // 가장 높은 평균 감정 찾기
        const topEmotion = Object.entries(averagedScores)
            .sort((a, b) => b[1] - a[1])[0];

        if (topEmotion && topEmotion[1] >= this.options.minConfidence) {
            return {
                emotion: topEmotion[0],
                confidence: topEmotion[1],
                allEmotions: averagedScores,
                timestamp: Date.now()
            };
        }

        return null;
    }

    /**
     * 감정 표시 업데이트
     * @param {Object} emotionData - 감정 데이터
     * @param {boolean} isPreviousState - 이전 상태를 표시하는지 여부
     */
    updateEmotionDisplay(emotionData, isPreviousState = false) {
        const displayEl = this.options.emotionDisplayElement;
        if (!displayEl) {
            console.warn('Emotion display element not found');
            return;
        }

        // HTML 구조에 맞게 직접 업데이트
        if (!emotionData) {
            displayEl.innerHTML = `
                <div class="no-data">얼굴을 인식할 수 없습니다</div>
            `;
            displayEl.style.background = 'var(--bg)';
            displayEl.style.borderColor = 'var(--border)';
            return;
        }

        const emotionInfo = this.emotionMap[emotionData.emotion] || this.emotionMap.neutral;
        const confidence = Math.round(emotionData.confidence * 100);
        
        // 이전 상태인 경우 표시
        const previousStateText = isPreviousState ? '<div style="font-size: 0.7rem; color: var(--text-light); opacity: 0.7; margin-top: 0.25rem;">(이전 감정)</div>' : '';

        displayEl.innerHTML = `
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">${emotionInfo.emoji}</div>
            <div style="font-size: 1rem; font-weight: 600; color: ${emotionInfo.color}; margin-bottom: 0.25rem;">${emotionInfo.label}</div>
            <div style="font-size: 0.85rem; color: var(--text-light);">신뢰도: ${confidence}%</div>
            ${previousStateText}
        `;

        // 배경색 업데이트 (이전 상태인 경우 약간 투명하게)
        const opacity = isPreviousState ? '10' : '15';
        displayEl.style.background = `${emotionInfo.color}${opacity}`;
        displayEl.style.borderColor = emotionInfo.color;
        displayEl.style.transition = 'all 0.3s ease';
        
        // 이전 상태인 경우 약간 투명하게
        if (isPreviousState) {
            displayEl.style.opacity = '0.8';
        } else {
            displayEl.style.opacity = '1';
        }
    }

    /**
     * 현재 감정 가져오기
     */
    getCurrentEmotion() {
        return this.currentEmotion;
    }

    /**
     * 감정 히스토리 가져오기
     */
    getEmotionHistory() {
        return [...this.emotionHistory];
    }

    /**
     * 평균 감정 계산
     */
    getAverageEmotion(count = 5) {
        const recent = this.emotionHistory.slice(-count);
        if (recent.length === 0) return null;

        const emotionScores = {};
        recent.forEach(entry => {
            Object.entries(entry.allEmotions).forEach(([emotion, score]) => {
                if (!emotionScores[emotion]) {
                    emotionScores[emotion] = 0;
                }
                emotionScores[emotion] += score;
            });
        });

        // 평균 계산
        Object.keys(emotionScores).forEach(emotion => {
            emotionScores[emotion] /= recent.length;
        });

        // 가장 높은 감정 찾기
        const topEmotion = Object.entries(emotionScores)
            .sort((a, b) => b[1] - a[1])[0];

        return {
            emotion: topEmotion[0],
            confidence: topEmotion[1],
            allEmotions: emotionScores
        };
    }

    /**
     * 현재 비디오 프레임을 이미지로 캡처
     * @returns {string|null} Base64 인코딩된 이미지 데이터 URL (data:image/jpeg;base64,...) 또는 null
     */
    captureImage() {
        const video = this.options.videoElement;
        const canvas = this.options.canvasElement;

        if (!video || !canvas || !this.modelsLoaded) {
            console.warn('Cannot capture image: missing video, canvas, or models not loaded');
            return null;
        }

        // 비디오가 준비되지 않았으면 null 반환
        if (video.readyState < video.HAVE_METADATA) {
            console.warn('Video not ready for capture');
            return null;
        }

        try {
            // Canvas 크기 업데이트 (비디오 크기에 맞춤)
            if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
                canvas.width = video.videoWidth || 640;
                canvas.height = video.videoHeight || 480;
            }

            // Canvas에 비디오 프레임 그리기
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

            // Canvas를 JPEG 이미지로 변환 (base64)
            const imageDataUrl = canvas.toDataURL('image/jpeg', 0.85); // 85% 품질
            
            // data:image/jpeg;base64, 부분을 제거하고 순수 base64만 반환
            const base64Data = imageDataUrl.split(',')[1];
            
            return base64Data;
        } catch (error) {
            console.error('Error capturing image:', error);
            return null;
        }
    }
}

