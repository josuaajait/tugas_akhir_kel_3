<?php
declare(strict_types=1);

$mode = $argv[1] ?? '';
if (!in_array($mode, ['reference', 'candidate'], true)) {
    fwrite(STDERR, "Invalid mode\n"); exit(2);
}
require '/opt/critic-runtime.php';
runHarness($mode === 'candidate', 'phpunit.xml', $mode === 'candidate' ? 'Internal' : null);
