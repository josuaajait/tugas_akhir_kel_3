<?php
// Trusted response-only probe. Never boots Laravel or executes a controller.
require $argv[1];
require $argv[2];
(new PHPUnit\TextUI\Configuration\Builder)->build(['final-probe','--no-configuration']);
$expected=[11=>['name'=>'one'],12=>['name'=>'two']];
$valid=['{"data":[{"id":11,"name":"one"},{"id":12,"name":"two"}]}',
        '{"data":[{"id":12,"name":"two","extra":1},{"id":11,"name":"one"}]}'];
$bad=['{"data":{"0":{"id":11,"name":"one"},"1":{"id":12,"name":"two"}}}',
      '{"data":[{"id":11,"name":"two"},{"id":12,"name":"one"}]}',
      '{"data":[{"id":11,"name":"one"},{"id":11,"name":"one"}]}',
      '{"data":[{"id":"11","name":"one"},{"id":12,"name":"two"}]}',
      '{"data":[{"id":11},{"id":12,"name":"two"}]}',
      '{"data":[{"id":13,"name":"one"},{"id":12,"name":"two"}]}',
      '{"data":[[11,"one"],[12,"two"]]}','[]'];
foreach($valid as $raw) FinalEvaluation\Assertions::collection($raw,$expected);
foreach($bad as $raw) {
    try { FinalEvaluation\Assertions::collection($raw,$expected); exit(4); }
    catch(PHPUnit\Framework\AssertionFailedError $e) {}
}
FinalEvaluation\Assertions::record('{"data":{"id":11,"name":"one"}}',11,['name'=>'one']);
foreach (['[]','{"data":[]}'] as $raw) {
    try { FinalEvaluation\Assertions::record($raw,11,['name'=>'one']); exit(5); }
    catch(PHPUnit\Framework\AssertionFailedError $e) {}
}
echo json_encode(['valid_collections_accepted'=>2,'invalid_collections_rejected'=>8,'valid_records_accepted'=>1,'invalid_records_rejected'=>2]);
