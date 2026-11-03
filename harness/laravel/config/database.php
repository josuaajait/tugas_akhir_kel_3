<?php
return [
    'default' => 'sqlite',
    'connections' => [
        'sqlite' => ['driver' => 'sqlite', 'database' => env('DB_DATABASE', ':memory:'),
                     'prefix' => '', 'foreign_key_constraints' => true],
    ],
    'migrations' => ['table' => 'migrations', 'update_date_on_publish' => true],
];
