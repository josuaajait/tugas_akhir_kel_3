<?php
// Trusted image entrypoint; controller execution occurs only inside this container.
declare(strict_types=1);

function copyTree(string $source, string $destination): void
{
    if (!is_dir($destination) && !mkdir($destination, 0700, true)) {
        throw new RuntimeException('Cannot create workspace');
    }
    foreach (new DirectoryIterator($source) as $entry) {
        if ($entry->isDot()) continue;
        if ($entry->isLink()) throw new RuntimeException('Unexpected symlink in image');
        $target = $destination.'/'.$entry->getFilename();
        if ($entry->isDir()) copyTree($entry->getPathname(), $target);
        elseif (!copy($entry->getPathname(), $target)) throw new RuntimeException('Copy failed');
    }
}

$mode = $argv[1] ?? '';
if (!in_array($mode, ['reference', 'candidate'], true)) {
    fwrite(STDERR, "Invalid mode\n"); exit(2);
}
copyTree('/opt/harness', '/work/app');
if ($mode === 'candidate' && !copy('/input/controller.php', '/work/app/app/Http/Controllers/ProductController.php')) {
    fwrite(STDERR, "Cannot stage candidate\n"); exit(2);
}
chdir('/work/app');
$args = ['php', '-d', 'memory_limit=256M', 'vendor/bin/phpunit', '--do-not-cache-result',
         '--log-junit', '/work/junit.xml'];
if ($mode === 'candidate') {
    $args[] = '--testsuite'; $args[] = 'Internal';
}
$process = proc_open($args, [STDIN, STDOUT, STDERR], $pipes, '/work/app');
if (!is_resource($process)) exit(2);
$exitCode = proc_close($process);
if (!is_file('/work/junit.xml') || is_link('/work/junit.xml') || filesize('/work/junit.xml') > 4000000) {
    fwrite(STDERR, "JUnit missing/invalid/oversized\n"); exit(2);
}
$xml = file_get_contents('/work/junit.xml');
if ($xml === false) exit(2);
echo "\nCRITIC_JUNIT_B64:".base64_encode($xml)."\n";
exit($exitCode);
