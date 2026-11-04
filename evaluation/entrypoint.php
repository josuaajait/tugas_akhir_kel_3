<?php
declare(strict_types=1);

$mode = $argv[1] ?? '';
if (!in_array($mode, ['evaluation-reference', 'evaluation-candidate'], true)) {
    fwrite(STDERR, "Evaluator accepts evaluation modes only\n"); exit(2);
}
if ($mode === 'evaluation-candidate') {
    // Lint inside the evaluator's exact PHP version; this never includes/evaluates the candidate.
    $process = proc_open(['php', '-n', '-l', '/input/controller.php'],
        [0 => STDIN, 1 => ['pipe', 'w'], 2 => STDERR], $pipes);
    if (!is_resource($process)) exit(2);
    $diagnostic = stream_get_contents($pipes[1], 16385);
    fclose($pipes[1]);
    $lintExit = proc_close($process);
    if ($lintExit !== 0) {
        if (is_string($diagnostic) && strlen($diagnostic) <= 16384
            && str_contains($diagnostic, 'Errors parsing /input/controller.php')) {
            echo 'CRITIC_INVALID_SYNTAX:'.base64_encode($diagnostic)."\n";
            exit(65);
        }
        fwrite(STDERR, "Syntax preflight failed without a parse diagnostic\n"); exit(2);
    }
}
require '/opt/critic-runtime.php';
runHarness($mode === 'evaluation-candidate', 'phpunit-evaluation.xml', 'ReferenceEvaluation');
