using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public delegate void CallbackTouch();

public class TouchManager : MonoBehaviour
{
    // 회전할 각도
    private float rotationAngle = 270.0f;
    // 회전에 걸리는 시간 (초)
    private float duration = 1.0f;
    private int repetition = 12;

    Ray ray;
	RaycastHit hit;

    CallbackTouch _callbackTouch;

    // Start is called before the first frame update
    void Start()
    {
        transform.localScale = new Vector3(0.3f, 0.3f, 0.3f);
        StartCoroutine(ScaleOverTime(3f));
        StartCoroutine(RotateOverTime(rotationAngle, duration));
    }

    // Update is called once per frame
    void Update()
    {
        ray = Camera.main.ScreenPointToRay(Input.mousePosition);
        if(Physics.Raycast(ray, out hit)) {
            if (Input.GetMouseButtonDown(0))
            {
                StartCoroutine(RotateOverTime(rotationAngle, duration));
                if (_callbackTouch != null) {
                    _callbackTouch();
                }
            }
        }
    }

    public void SetTouchCallback(CallbackTouch callback)
    {
        if (_callbackTouch == null) {
            _callbackTouch = callback;
        } else {
            _callbackTouch += callback;
        }
    }

    IEnumerator RotateOverTime(float angle, float time)
    {
        for (int i = 0; i < repetition; i++) {
            // 회전을 시작할 때의 회전값
            Quaternion startRotation = transform.rotation;
            // 회전을 끝낼 때의 회전값
            Quaternion endRotation = transform.rotation * Quaternion.Euler(0, angle, 0);
            // 경과된 시간을 추적하는 변수
            float elapsed = 0.0f;

            while (elapsed < time)
            {
                // 경과된 시간을 업데이트합니다.
                elapsed += Time.deltaTime;
                // Lerp 함수를 사용하여 부드럽게 회전시킵니다.
                transform.rotation = Quaternion.Lerp(startRotation, endRotation, elapsed / time);
                // Debug.Log("rotation: " + transform.rotation);
                // 다음 프레임까지 기다립니다.
                yield return null;
            }

            // 정확한 회전 각도를 위해 마지막으로 설정합니다.
            transform.rotation = endRotation;
        }
    }

    IEnumerator ScaleOverTime(float time)
    {
        Vector3 originalScale = transform.localScale; // 현재 스케일
        Vector3 targetScale = new Vector3(0.7f, 0.7f, 0.7f); // 목표 스케일

        float currentTime = 0.0f;

        do
        {
            // Lerp 함수를 사용하여 점진적으로 scale 값을 변경
            transform.localScale = Vector3.Lerp(originalScale, targetScale, currentTime / time);
            currentTime += Time.deltaTime; // 현재 경과 시간 업데이트
            yield return null; // 다음 프레임까지 기다림
        } while (currentTime <= time);

        transform.localScale = targetScale; // 마지막으로 scale 값을 정확하게 목표값으로 설정
    }
}