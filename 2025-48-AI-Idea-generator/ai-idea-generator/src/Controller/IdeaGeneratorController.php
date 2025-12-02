<?php

namespace App\Controller;

use App\DTO\IdeaRequest;
use App\Service\IdeaGeneratorService;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

final class IdeaGeneratorController extends AbstractController
{
    public function __construct(
        private readonly IdeaGeneratorService $ideaGeneratorService
    ) {
    }

    #[Route('/', name: 'app_idea_generator')]
    public function index(Request $request): Response
    {
        $ideaRequest = $this->readRequestDTO($request);
        $ideas = null;

        if ($ideaRequest instanceof IdeaRequest) {
            $ideas = $this->ideaGeneratorService->generateIdea($ideaRequest);
        }

        return $this->render(
            'idea_generator/index.html.twig',
            [
                'ideaRequest' => $ideaRequest,
                'ideas' => $ideas,
            ]
        );
    }

    private function readRequestDTO(Request $request): ?IdeaRequest
    {
        if ($request->getMethod() !== Request::METHOD_POST) {
            return null;
        }

        $model = $request->request->get('model', null);
        $apiKey = $request->request->get('api-key', null);
        $age = $request->request->get('age', null);
        $interests = $request->request->get('interests', null);
        $count = $request->request->get('count', null);

        $error = match (true) {
            $model === null || !is_string($model) => 'Model is required and must be a string.',
            $apiKey === null || !is_string($apiKey) => 'API Key is required and must be a string.',
            $age === null || !is_numeric($age) => 'Age is required and must be a number.',
            $interests === null || !is_string($interests) => 'Interests are required and must be a string.',
            $count === null || !is_numeric($count) => 'Count is required and must be a number.',
            default => null,
        };

        if ($error !== null) {
            throw new \InvalidArgumentException($error);
        }

        return new IdeaRequest(
            model: $model,
            apiKey: $apiKey,
            age: intval($age),
            interests: $interests,
            count: intval($count),
        );
    }
}
