from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


# ==========================================================
# Chunk Configuration
# ==========================================================

class ChunkConfiguration(BaseModel):

    chunk_size: int = Field(
        ge=500,
        le=8000,
    )

    chunk_overlap: int = Field(
        ge=0,
        le=2000,
    )


    @model_validator(
        mode="after"
    )
    def validate_overlap(
        self,
    ):

        if (
            self.chunk_overlap
            >= self.chunk_size
        ):

            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        return self


# ==========================================================
# Automated Optimization Request
# ==========================================================

class RAGOptimizationRequest(BaseModel):

    document_id: int = Field(
        ge=1
    )

    chunk_configs: list[
        ChunkConfiguration
    ]

    top_k_values: list[int]

    threshold_values: list[float]

    restore_best_index: bool = True


    @model_validator(
        mode="after"
    )
    def validate_experiment(
        self,
    ):

        # --------------------------------------------------
        # Required values
        # --------------------------------------------------

        if not self.chunk_configs:

            raise ValueError(
                "At least one chunk configuration is required"
            )


        if not self.top_k_values:

            raise ValueError(
                "At least one top_k value is required"
            )


        if not self.threshold_values:

            raise ValueError(
                "At least one threshold value is required"
            )


        # --------------------------------------------------
        # Validate Top-K
        # --------------------------------------------------

        for top_k in self.top_k_values:

            if (
                top_k < 1
                or top_k > 20
            ):

                raise ValueError(
                    "top_k values must be between 1 and 20"
                )


        # --------------------------------------------------
        # Validate Threshold
        # --------------------------------------------------

        for threshold in self.threshold_values:

            if (
                threshold < 0
                or threshold > 1
            ):

                raise ValueError(
                    "threshold values must be between 0 and 1"
                )


        # --------------------------------------------------
        # Protect against accidentally running
        # a huge number of expensive experiments.
        # --------------------------------------------------

        total_combinations = (
            len(self.chunk_configs)
            * len(self.top_k_values)
            * len(self.threshold_values)
        )


        if total_combinations > 27:

            raise ValueError(
                "Maximum 27 experiment combinations are allowed"
            )


        return self