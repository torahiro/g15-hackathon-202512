import time

class TalkTimer:
    def __init__(self, penalty_limit=30, silence_tolerance=2.0):
        self.speech_start_time = None
        self.last_sound_time = 0
        self.is_talking_session = False
        self.penalty_limit = penalty_limit
        self.silence_tolerance = silence_tolerance

    def update(self, is_talking_now):
        current_time = time.time()
        
        # 音がある場合
        if is_talking_now:
            self.last_sound_time = current_time
            if not self.is_talking_session:
                self.is_talking_session = True
                self.speech_start_time = current_time
        
        # 音がない場合でも、許容範囲内ならセッション継続
        elif self.is_talking_session:
            if current_time - self.last_sound_time > self.silence_tolerance:
                self.is_talking_session = False
                self.speech_start_time = None

        # 継続時間を計算
        if self.is_talking_session and self.speech_start_time:
            duration = current_time - self.speech_start_time
            return duration
        
        return 0.0