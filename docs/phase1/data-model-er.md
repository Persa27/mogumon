# データモデル（ER概要・フェーズ1）

## 1. エンティティ
- users
- child_profiles
- meal_sessions
- tap_events
- monster_states
- food_attribute_ledgers

## 2. 関係
- users 1 - N child_profiles
- child_profiles 1 - N meal_sessions
- meal_sessions 1 - N tap_events
- child_profiles 1 - 1 monster_states
- child_profiles 1 - N food_attribute_ledgers

## 3. 主要属性（抜粋）
### meal_sessions
- id
- child_profile_id
- started_at
- finished_at
- total_points
- max_combo

### tap_events
- id
- meal_session_id
- tapped_at
- is_valid
- combo_count
- food_type
- granted_points

### monster_states
- child_profile_id
- level
- growth_points
- evolution_type
