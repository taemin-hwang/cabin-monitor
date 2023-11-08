using UnityEngine;
using UnityEngine.UI;
using System.Collections;

public class ScreenFade : MonoBehaviour
{
    public Image fadeImage; // Inspector에서 할당하세요.
    public float fadeDuration = 2f; // 페이드 지속 시간

    private void Start()
    {
        // 페이드 인을 시작합니다. (화면을 밝게)
        StartCoroutine(FadeIn());
    }

    IEnumerator FadeIn()
    {
        float elapsedTime = 0f;

        // 시작할 때 이미지를 불투명하게 설정합니다.
        Color startColor = fadeImage.color;
        startColor.a = 1f;
        fadeImage.color = startColor;

        // 페이드 인 동안 이미지의 투명도를 점차 감소시킵니다.
        while (elapsedTime < fadeDuration)
        {
            elapsedTime += Time.deltaTime;
            float alpha = 1 - (elapsedTime / fadeDuration);
            fadeImage.color = new Color(startColor.r, startColor.g, startColor.b, alpha);
            yield return null;
        }

        // 페이드 인이 끝나면 완전히 투명하게 설정합니다.
        fadeImage.color = new Color(startColor.r, startColor.g, startColor.b, 0);
    }

    // 페이드 아웃을 시작하려면 이 함수를 호출하세요.
    public IEnumerator FadeOut()
    {
        float elapsedTime = 0f;
        Color startColor = fadeImage.color;
        startColor.a = 0f;
        fadeImage.color = startColor;

        // 페이드 아웃 동안 이미지의 투명도를 점차 증가시킵니다.
        while (elapsedTime < fadeDuration)
        {
            elapsedTime += Time.deltaTime;
            float alpha = elapsedTime / fadeDuration;
            fadeImage.color = new Color(startColor.r, startColor.g, startColor.b, alpha);
            yield return null;
        }

        // 페이드 아웃이 끝나면 완전히 불투명하게 설정합니다.
        fadeImage.color = new Color(startColor.r, startColor.g, startColor.b, 1);
    }
}