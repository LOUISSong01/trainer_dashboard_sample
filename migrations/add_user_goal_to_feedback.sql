-- data_trainer_feedback 테이블에 user_goal 컬럼 추가
-- 사용자의 목표(체중 감량, 근육 증가 등)를 저장하여 더 구체적인 피드백 제공

ALTER TABLE data_trainer_feedback 
ADD COLUMN IF NOT EXISTS user_goal VARCHAR(50);

-- 기존 데이터에 기본값 설정 (선택사항)
UPDATE data_trainer_feedback 
SET user_goal = '일반' 
WHERE user_goal IS NULL;

-- 인덱스 추가 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_feedback_user_goal 
ON data_trainer_feedback(user_goal);

-- 확인
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'data_trainer_feedback' 
AND column_name = 'user_goal';

