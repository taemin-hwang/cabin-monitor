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
    private int repetition = 5;

    Ray ray;
	RaycastHit hit;

    CallbackTouch _callbackTouch;

    // Start is called before the first frame update
    void Start()
    {

    }

    // Update is called once per frame
    void Update()
    {
        ray = Camera.main.ScreenPointToRay(Input.mousePosition);
        if(Physics.Raycast(ray, out hit)) {
        #if UNITY_EDITOR
            // 마우스 클릭 시
            if (Input.GetMouseButtonDown(0))
        #else
            // 터치 시
            if (Input.touchCount > 0)
        #endif
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


}
