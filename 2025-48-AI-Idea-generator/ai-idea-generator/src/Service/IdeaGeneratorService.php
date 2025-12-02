<?php

declare(strict_types=1);

namespace App\Service;

use App\DTO\IdeaRequest;
use App\Entity\Idea;
use Symfony\AI\Platform\Bridge\Gemini\PlatformFactory as GeminiPlatformFactory;
use Symfony\AI\Platform\Bridge\OpenAi\PlatformFactory as OpenAiPlatformFactory;
use Symfony\AI\Platform\Bridge\Mistral\PlatformFactory as MistralPlatformFactory;
use Symfony\AI\Platform\Bridge\Anthropic\PlatformFactory as AnthropicPlatformFactory;
use Symfony\AI\Platform\Message\Message;
use Symfony\AI\Platform\Message\MessageBag;
use Symfony\AI\Platform\PlatformInterface;
use Symfony\Component\Serializer\SerializerInterface;

final class IdeaGeneratorService
{
    public function __construct(
        private readonly SerializerInterface $serializer,
    ) {
    }
    /**
     * @return Idea[]
     */
    public function generateIdea(IdeaRequest $ideaRequest): array
    {
        $result = $this->getPlatform($ideaRequest)->invoke(
            $ideaRequest->model,
            new MessageBag(
                Message::forSystem($this->getSystemPrompt()),
                Message::ofUser($this->getUserPrompt($ideaRequest)),
            ),
        );

        return $this->serializer->deserialize(
            $this->formatResultText($result->asText()),
            Idea::class . '[]',
            'json',
        );
    }

    private function getPlatform(IdeaRequest $ideaRequest): PlatformInterface
    {
        $gemini = GeminiPlatformFactory::create($ideaRequest->apiKey);

        if(array_key_exists(
            $ideaRequest->model,
            $gemini->getModelCatalog()->getModels(),
        )) {
            return $gemini;
        }

        $openai = OpenAiPlatformFactory::create($ideaRequest->apiKey);

        if(array_key_exists(
            $ideaRequest->model,
            $openai->getModelCatalog()->getModels(),
        )) {
            return $openai;
        }

        $mistral = MistralPlatformFactory::create($ideaRequest->apiKey);

        if(array_key_exists(
            $ideaRequest->model,
            $mistral->getModelCatalog()->getModels(),
        )) {
            return $mistral;
        }

        $anthropic = AnthropicPlatformFactory::create($ideaRequest->apiKey);

        if(array_key_exists(
            $ideaRequest->model,
            $anthropic->getModelCatalog()->getModels(),
        )) {
            return $anthropic;
        }

        throw new \InvalidArgumentException('Le modèle spécifié n\'est pas disponible.');
    }

    private function getSystemPrompt(): string
    {
        return <<<PROMPT
            Tu es un assistant qui génère des idées créatives de cadeaux répondant aux caractéristiques spécifiques des personnes.
            Tu réponds toujours en français.
            Tes réponses doivent être du JSON valide (uniquement le contenu JSON, pas du markdown) sans explications supplémentaires.
            Le format de ta réponse doit être un tableau contenant des objets avec le format suivant :
            {
                "name": string,
                "price": float
            }
            ---
            name : "Nom du cadeau proposé"
            price : "Prix moyen estimé en euros avec deux décimales"
    PROMPT;
    }

    private function getUserPrompt(IdeaRequest $ideaRequest): string
    {
        return <<<PROMPT
            Génère une liste de {$ideaRequest->count} idées de cadeaux pour une personne ayant les caractéristiques suivantes :
            - Age : {$ideaRequest->age}
            - Centres d'intérêt : {$ideaRequest->interests}
    PROMPT;
    }

    private function formatResultText(string $text): string
    {
        $start = strpos($text, '[');
        $end = strrpos($text, ']');

        if ($start === false || $end === false) {
            throw new \RuntimeException('Le format de la réponse est invalide.');
        }

        return substr($text, $start, $end - $start + 1);
    }
}
