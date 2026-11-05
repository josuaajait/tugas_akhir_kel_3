<?php
namespace App\Http\Controllers;

use App\Models\Book;
use Illuminate\Http\Request;

// Controlled development fixture; labels require independent human review.
class BookController extends Controller
{
    public function index()
    {
        return response()->json(['data' => Book::all()], 200);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'title' => ['required', 'string', 'max:80'],
            'pages' => ['required', 'integer', 'min:1', 'max:5000'],
        ]);
        $book = Book::create($data);
        return response()->json(['data' => $book], 201);
    }

    public function lookup($id)
    {
        return response()->json(['data' => Book::findOrFail($id)], 200);
    }

    public function update(Request $request, $id)
    {
        $book = Book::findOrFail($id);
        $data = $request->validate([
            'title' => ['required', 'string', 'max:80'],
            'pages' => ['required', 'integer', 'min:1', 'max:5000'],
        ]);
        $book->update($data);
        return response()->json(['data' => $book->fresh()], 200);
    }

    public function destroy($id)
    {
        Book::findOrFail($id)->delete();
        return response()->noContent();
    }
}
