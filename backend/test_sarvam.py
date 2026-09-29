import os

from pathlib import Path

from dotenv import load_dotenv

from sarvamai import SarvamAI


load_dotenv(
    Path(__file__).resolve().parent
    / ".env"
)


api_key = os.getenv(
    "SARVAM_API_KEY"
)

model = os.getenv(
    "SARVAM_MODEL",
    "sarvam-105b",
)


if not api_key:

    raise ValueError(
        "SARVAM_API_KEY is missing "
        "from backend/.env"
    )


client = SarvamAI(
    api_subscription_key=api_key
)


print(
    "Connecting to Sarvam API..."
)


try:

    response = (
        client.chat.completions(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Reply with exactly: "
                        "Sarvam API connection "
                        "successful."
                    ),
                }
            ],
            temperature=0,
            max_tokens=100,
            reasoning_effort=None,
        )
    )

    print(
        "\nFull response:"
    )

    print(response)

    print(
        "\nMessage:"
    )

    print(
        response
        .choices[0]
        .message
    )

    print(
        "\nContent:"
    )

    print(
        response
        .choices[0]
        .message
        .content
    )

    print(
        "\nReasoning content:"
    )

    print(
        getattr(
            response
            .choices[0]
            .message,
            "reasoning_content",
            None,
        )
    )

except Exception as e:

    print(
        "\nSarvam API connection failed:"
    )

    print(
        type(e).__name__
    )

    print(
        str(e)
    )