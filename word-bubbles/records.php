<?php
// Word Bubbles Daily — best-time records (world / country / local) per board.
//
//   GET  records.php?id=d51-easy            -> {"record": {"ms": 41200, "pts": 120} | null}
//   POST records.php  {"id","ms","pts"}     -> {"record": {...}, "won": true|false}
//
// A record is the fastest finish, compared to the second; a tie on time goes to the
// higher score (same rule as the game's `beats`). The compare-and-write runs inside one
// locked SQLite transaction, so two people finishing at once can't overwrite each other.

header('Content-Type: application/json');
header('Cache-Control: no-store');

function reply($code, $body) {
    http_response_code($code);
    echo json_encode($body);
    exit;
}

// board id + optional "-c-<country>" or "-z-<local zone>", e.g. d51-hard-z-America~Toronto
function valid_id($id) {
    return is_string($id) && preg_match('/^d\d{1,5}-(easy|medium|hard)(-[cz]-[A-Za-z0-9~_.+-]{1,60})?$/', $id);
}

function db() {
    $dir = __DIR__ . '/data';
    if (!is_dir($dir)) mkdir($dir, 0755, true);
    $pdo = new PDO('sqlite:' . $dir . '/records.sqlite');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_TIMEOUT, 5);
    $pdo->exec('CREATE TABLE IF NOT EXISTS records (
        id  TEXT PRIMARY KEY,
        ms  INTEGER NOT NULL,
        pts INTEGER NOT NULL,
        at  TEXT NOT NULL
    )');
    return $pdo;
}

function find($pdo, $id) {
    $q = $pdo->prepare('SELECT ms, pts FROM records WHERE id = ?');
    $q->execute([$id]);
    $row = $q->fetch(PDO::FETCH_ASSOC);
    return $row ? ['ms' => (int)$row['ms'], 'pts' => (int)$row['pts']] : null;
}

function beats($a, $b) {
    if (!$b) return true;
    $sa = intdiv($a['ms'], 1000);
    $sb = intdiv($b['ms'], 1000);
    return $sa < $sb || ($sa === $sb && $a['pts'] > $b['pts']);
}

try {
    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        $id = $_GET['id'] ?? '';
        if ($id === 'ping') reply(200, ['record' => null]);
        if (!valid_id($id)) reply(400, ['error' => 'bad id']);
        reply(200, ['record' => find(db(), $id)]);
    }

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $in = json_decode(file_get_contents('php://input'), true);
        $id = $in['id'] ?? '';
        $ms = $in['ms'] ?? null;
        $pts = $in['pts'] ?? 0;
        if (!valid_id($id)) reply(400, ['error' => 'bad id']);
        // the game already drops impossible times (under 0.4s a bubble); this just bounds junk
        if (!is_int($ms) || $ms < 1000 || $ms > 86400000) reply(400, ['error' => 'bad ms']);
        if (!is_int($pts) || $pts < 0 || $pts > 100000) reply(400, ['error' => 'bad pts']);

        $mine = ['ms' => $ms, 'pts' => $pts];
        $pdo = db();
        $pdo->exec('BEGIN IMMEDIATE');
        $cur = find($pdo, $id);
        if (!beats($mine, $cur)) {
            $pdo->exec('COMMIT');
            reply(200, ['record' => $cur, 'won' => false]);
        }
        $w = $pdo->prepare('INSERT OR REPLACE INTO records (id, ms, pts, at) VALUES (?, ?, ?, ?)');
        $w->execute([$id, $ms, $pts, gmdate('c')]);
        $pdo->exec('COMMIT');
        reply(200, ['record' => $mine, 'won' => true]);
    }

    reply(405, ['error' => 'method not allowed']);
} catch (Throwable $e) {
    reply(500, ['error' => 'server error']);
}
