from app.core.config import settings

from app.llm.openai_provider import (
    generate_openai_response,
)

from app.llm.gemini_provider import (
    generate_gemini_response,
)


# ==========================================================
# Provider Registry
# ==========================================================

PROVIDERS = {

    "openai":
        generate_openai_response,

    "gemini":
        generate_gemini_response,
}


# ==========================================================
# Run One Provider
# ==========================================================

def run_provider(
    provider_name: str,
    messages: list[dict],
    system_prompt: str,
):

    provider_name = (
        provider_name
        .lower()
        .strip()
    )


    provider = PROVIDERS.get(
        provider_name
    )


    if provider is None:

        raise ValueError(
            f"Unsupported LLM provider: "
            f"{provider_name}"
        )


    return provider(
        messages=
            messages,

        system_prompt=
            system_prompt,
    )


# ==========================================================
# Multi-Provider Generation
#
# Primary
#    ↓ fail
# Fallback
# ==========================================================

def generate_llm_response(
    messages: list[dict],
    system_prompt: str,
    provider: str | None = None,
):

    # ------------------------------------------------------
    # Explicit provider override
    # ------------------------------------------------------

    if provider:

        return run_provider(

            provider_name=
                provider,

            messages=
                messages,

            system_prompt=
                system_prompt,
        )


    # ------------------------------------------------------
    # Primary provider
    # ------------------------------------------------------

    primary = (
        settings.LLM_PRIMARY_PROVIDER
        .lower()
        .strip()
    )


    try:

        result = run_provider(

            provider_name=
                primary,

            messages=
                messages,

            system_prompt=
                system_prompt,
        )


        result[
            "fallback_used"
        ] = False


        return result


    except Exception as primary_error:

        print(
            "PRIMARY LLM ERROR:",
            primary,
            type(primary_error).__name__,
            str(primary_error),
        )


        # --------------------------------------------------
        # Fallback disabled
        # --------------------------------------------------

        fallback = (
            settings.LLM_FALLBACK_PROVIDER
        )


        if not fallback:

            raise


        fallback = (
            fallback
            .lower()
            .strip()
        )


        # Avoid trying same provider twice

        if fallback == primary:

            raise


        print(
            "LLM FALLBACK:",
            primary,
            "→",
            fallback,
        )


        try:

            result = run_provider(

                provider_name=
                    fallback,

                messages=
                    messages,

                system_prompt=
                    system_prompt,
            )


            result[
                "fallback_used"
            ] = True


            result[
                "failed_provider"
            ] = primary


            return result


        except Exception as fallback_error:

            print(
                "FALLBACK LLM ERROR:",
                fallback,
                type(
                    fallback_error
                ).__name__,
                str(
                    fallback_error
                ),
            )


            raise RuntimeError(
                "All configured LLM providers failed"
            ) from fallback_error