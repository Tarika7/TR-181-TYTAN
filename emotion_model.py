import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
import joblib
import os

class EmotionClassifier:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.is_trained = False
        self.model_path = 'emotion_model.pkl'

        # Load existing model if available
        if os.path.exists(self.model_path):
            try:
                self.load_model()
            except:
                print("Could not load existing model, will use rule-based fallback")

    def extract_features(self, landmarks):
        """Extract AU-like features from MediaPipe landmarks"""
        if not landmarks:
            return np.zeros(17)  # Return zero features for no face

        # Extract key facial points
        nose = landmarks[1]
        left_eye = landmarks[159]
        right_eye = landmarks[386]
        left_mouth = landmarks[61]
        right_mouth = landmarks[291]
        upper_lip = landmarks[13]
        lower_lip = landmarks[14]
        left_eyebrow = landmarks[70]
        right_eyebrow = landmarks[300]
        chin = landmarks[152]

        # Calculate distances and ratios (simulating AU features)
        features = []

        # AU1: Inner brow raiser (eyebrow height relative to eyes)
        features.append((left_eyebrow.y - left_eye.y) / abs(left_eye.y - nose.y + 0.001))
        features.append((right_eyebrow.y - right_eye.y) / abs(right_eye.y - nose.y + 0.001))

        # AU2: Outer brow raiser
        features.append(left_eyebrow.y - nose.y)
        features.append(right_eyebrow.y - nose.y)

        # AU4: Brow lowerer
        features.append(nose.y - left_eyebrow.y)
        features.append(nose.y - right_eyebrow.y)

        # AU5: Upper lid raiser (eye openness)
        features.append(left_eye.y - nose.y)
        features.append(right_eye.y - nose.y)

        # AU6: Cheek raiser (not directly available, using mouth proximity)
        features.append(abs(left_mouth.x - nose.x))
        features.append(abs(right_mouth.x - nose.x))

        # AU7: Lid tightener (not available, using eye proximity to nose)
        features.append(abs(left_eye.x - nose.x))
        features.append(abs(right_eye.x - nose.x))

        # AU12: Lip corner puller (mouth width)
        mouth_width = abs(right_mouth.x - left_mouth.x)
        features.append(mouth_width)

        # AU15: Lip corner depressor (mouth width variation)
        features.append(mouth_width / abs(nose.x - chin.x + 0.001))

        # AU17: Chin raiser (not available, using lip height)
        lip_height = abs(upper_lip.y - lower_lip.y)
        features.append(lip_height)

        # AU20: Lip stretcher (mouth width relative to face)
        face_width = abs(landmarks[234].x - landmarks[454].x)  # temple points
        features.append(mouth_width / (face_width + 0.001))

        # AU23: Lip tightener (lip height relative to width)
        features.append(lip_height / (mouth_width + 0.001))

        # AU25: Lips part (vertical mouth opening)
        features.append(abs(upper_lip.y - lower_lip.y))

        # AU26: Jaw drop (distance from nose to chin)
        features.append(abs(nose.y - chin.y))

        return np.array(features)

    def train_sample_model(self):
        """Train on synthetic data simulating FER2013-like distributions"""
        np.random.seed(42)

        # Generate synthetic AU features for each emotion
        n_samples = 100

        # Engaged: High AU12 (smile), moderate AU5 (eye open), low AU4 (brow lower)
        engaged_features = np.random.normal([0.1, 0.1, 0.1, 0.1, -0.1, -0.1, 0.1, 0.1, 0.1, 0.1, 0.2, 0.2, 0.15, 0.1, 0.1, 0.1, 0.1],
                                          [0.05, 0.05, 0.05, 0.05, 0.03, 0.03, 0.05, 0.05, 0.05, 0.05, 0.1, 0.1, 0.05, 0.03, 0.03, 0.03, 0.03],
                                          (n_samples, 17))

        # Confused: Moderate brow raise (AU1/AU2), neutral mouth
        confused_features = np.random.normal([0.05, 0.05, 0.05, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.1, 0.08, 0.05, 0.05, 0.05, 0.05],
                                           [0.03, 0.03, 0.03, 0.03, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.05, 0.05, 0.03, 0.02, 0.02, 0.02, 0.02],
                                           (n_samples, 17))

        # Frustrated: Brow lower (AU4), lip tightener (AU23), reduced eye opening
        frustrated_features = np.random.normal([-0.05, -0.05, -0.05, -0.05, 0.1, 0.1, -0.05, -0.05, -0.05, -0.05, 0.05, 0.05, 0.05, 0.02, 0.02, 0.02, 0.02],
                                             [0.03, 0.03, 0.03, 0.03, 0.05, 0.05, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.02, 0.01, 0.01, 0.01, 0.01],
                                             (n_samples, 17))

        # Bored: Reduced AU5 (eye closing), neutral expressions
        bored_features = np.random.normal([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.1, -0.1, -0.1, -0.1, 0.0, 0.0, 0.03, 0.01, 0.01, 0.01, 0.01],
                                        [0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.05, 0.05, 0.05, 0.05, 0.02, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01],
                                        (n_samples, 17))

        # Combine features and labels
        X = np.vstack([engaged_features, confused_features, frustrated_features, bored_features])
        y = np.array([0] * n_samples + [1] * n_samples + [2] * n_samples + [3] * n_samples)  # 0=Engaged, 1=Confused, 2=Frustrated, 3=Bored

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)

        # Train SVM
        self.model = SVC(kernel='rbf', C=1.0, gamma='scale', probability=True)
        self.model.fit(X_scaled, y)

        self.is_trained = True
        self.save_model()

        print("Emotion classifier trained on synthetic data")

    def predict_emotion(self, landmarks):
        """Predict emotion from landmarks"""
        if not self.is_trained:
            return self.rule_based_fallback(landmarks)

        features = self.extract_features(landmarks)
        features_scaled = self.scaler.transform([features])

        prediction = self.model.predict(features_scaled)[0]
        confidence = np.max(self.model.predict_proba(features_scaled))

        emotions = ['Engaged', 'Confused', 'Frustrated', 'Bored']
        predicted_emotion = emotions[prediction]

        # Use rule-based fallback if confidence is low
        if confidence < 0.6:
            fallback = self.rule_based_fallback(landmarks)
            return fallback

        return predicted_emotion

    def rule_based_fallback(self, landmarks):
        """Simple rule-based emotion detection as fallback"""
        if not landmarks:
            return "No Face"

        # Simple heuristics based on facial features
        left_mouth = landmarks[61]
        right_mouth = landmarks[291]
        upper_lip = landmarks[13]
        lower_lip = landmarks[14]
        eye = landmarks[159]
        brow = landmarks[70]

        mouth_open = abs(upper_lip.y - lower_lip.y)
        mouth_width = abs(left_mouth.x - right_mouth.x)
        eye_open = eye.y
        brow_height = brow.y

        if mouth_open < 0.01 and brow_height < 0.3:
            return "Frustrated"
        elif eye_open < 0.2:
            return "Bored"
        elif mouth_width > 0.1:
            return "Engaged"
        else:
            return "Confused"

    def save_model(self):
        """Save trained model to disk"""
        if self.is_trained:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained
            }
            joblib.dump(model_data, self.model_path)

    def load_model(self):
        """Load trained model from disk"""
        model_data = joblib.load(self.model_path)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.is_trained = model_data['is_trained']

# Global classifier instance
classifier = EmotionClassifier()
if not classifier.is_trained:
    classifier.train_sample_model()
