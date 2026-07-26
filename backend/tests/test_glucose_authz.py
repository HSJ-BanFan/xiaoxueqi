def glucose_payload(user_id: str, value: float = 6.5) -> dict:
    return {
        "user_id": user_id,
        "value": value,
        "measurement_time": "BEFORE_BREAKFAST",
        "measurement_method": "FINGER_STICK",
        "notes": "pytest",
    }


def test_g1_user_creates_own_glucose(client, user_a, auth_header_a):
    response = client.post(
        "/api/v1/glucose",
        headers=auth_header_a,
        json=glucose_payload(user_a.id),
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == user_a.id


def test_g2_list_only_contains_current_users_records(
    client,
    user_a,
    user_b,
    auth_header_a,
    auth_header_b,
):
    response_a = client.post(
        "/api/v1/glucose",
        headers=auth_header_a,
        json=glucose_payload(user_a.id, 6.1),
    )
    response_b = client.post(
        "/api/v1/glucose",
        headers=auth_header_b,
        json=glucose_payload(user_b.id, 8.8),
    )
    assert response_a.status_code == response_b.status_code == 200

    response = client.get("/api/v1/glucose", headers=auth_header_a)
    ids = {item["id"] for item in response.json()}

    assert response_a.json()["id"] in ids
    assert response_b.json()["id"] not in ids


def test_g3_user_cannot_read_another_users_record(
    client,
    user_a,
    user_b,
    auth_header_a,
    auth_header_b,
):
    created = client.post(
        "/api/v1/glucose",
        headers=auth_header_b,
        json=glucose_payload(user_b.id),
    )

    response = client.get(
        f"/api/v1/glucose/{created.json()['id']}",
        headers=auth_header_a,
    )

    assert response.status_code in (403, 404)


def test_g4_body_user_id_mismatch_is_forbidden(client, user_a, user_b, auth_header_a):
    response = client.post(
        "/api/v1/glucose",
        headers=auth_header_a,
        json=glucose_payload(user_b.id),
    )

    assert response.status_code == 403


def test_g5_empty_statistics_do_not_fail(client, auth_header_a):
    response = client.get(
        "/api/v1/glucose/statistics?period=week",
        headers=auth_header_a,
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
