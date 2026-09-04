from typing import List, Tuple, Dict, Any
from app.models.entities import Observation, CandidateEntity, CandidateEntityLink
from app.models.enums import EntityType, IdentityStatus

def extract_features_from_observation(obs: Observation) -> Dict[str, Any]:
    raw = obs.raw_data or {}
    features = {}
    if "attributes" in raw:
        features.update(raw["attributes"])
    if "clothing" in raw:
        features["clothing"] = raw["clothing"]
    if "vehicle_type" in raw:
        features["vehicle_type"] = raw["vehicle_type"]
    if "license_plate" in raw:
        features["license_plate"] = raw["license_plate"]
    if "item_name" in raw:
        features["item_name"] = raw["item_name"]
    return features

def calculate_person_match_score(entity_desc: Dict[str, Any], obs_features: Dict[str, Any]) -> Tuple[float, Dict[str, Any], str]:
    matched_features = []
    score = 0.50

    entity_clothing = str(entity_desc.get("clothing", "")).lower()
    obs_clothing = str(obs_features.get("clothing", "")).lower()

    if "jacket" in entity_clothing and "jacket" in obs_clothing:
        score += 0.20
        matched_features.append("jacket match")
        if ("dark" in entity_clothing or "black" in entity_clothing) and ("dark" in obs_clothing or "black" in obs_clothing):
            score += 0.15
            matched_features.append("dark/black color match")

    if "backpack" in str(obs_features) or "bag" in str(obs_features):
        score += 0.05
        matched_features.append("carrying bag/backpack")

    return min(score, 0.95), {"matching_features": matched_features}, "clothing_similarity"

def match_observation_to_entity(
    entity: CandidateEntity,
    obs: Observation
) -> Tuple[bool, float, Dict[str, Any], str]:
    obs_features = extract_features_from_observation(obs)

    if entity.entity_type == EntityType.PERSON:
        score, evidence, method = calculate_person_match_score(entity.description or {}, obs_features)
        # Match threshold 0.50
        if score >= 0.55:
            return True, score, evidence, method
        return False, 0.0, {}, method

    elif entity.entity_type == EntityType.VEHICLE:
        entity_plate = entity.description.get("license_plate", "")
        obs_plate = obs_features.get("license_plate", "")
        if entity_plate and obs_plate and (entity_plate in obs_plate or obs_plate in entity_plate):
            return True, 0.95, {"plate_match": [entity_plate, obs_plate]}, "plate_exact_match"
        return False, 0.0, {}, "vehicle_attributes"

    elif entity.entity_type == EntityType.ITEM:
        entity_name = str(entity.description.get("item_name", "")).lower()
        obs_name = str(obs_features.get("item_name", "")).lower()
        if entity_name and obs_name and (entity_name in obs_name or obs_name in entity_name):
            return True, 0.90, {"item_match": [entity_name, obs_name]}, "item_descriptor_match"
        return False, 0.0, {}, "item_matching"

    return False, 0.0, {}, "unknown"
