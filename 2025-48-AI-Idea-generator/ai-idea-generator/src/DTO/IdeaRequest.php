<?php

declare(strict_types=1);

namespace App\DTO;

final class IdeaRequest
{
    public function __construct(
        public readonly string $model,
        public readonly string $apiKey,
        public readonly int $age,
        public readonly string $interests,
        public readonly int $count,
    ) {
    }
}
