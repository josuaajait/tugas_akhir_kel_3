<?php

namespace App\Http\Controllers;

use App\Models\Product;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

// Trusted readiness reference. Not a generated candidate or independent oracle.
class ProductController extends Controller
{
    public function index()
    {
        return response()->json(['data' => Product::all()], 200);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:100'],
            'price' => ['required', 'integer', 'min:0'],
            'sku' => ['required', 'string', 'unique:products,sku'],
        ]);
        return response()->json(['data' => Product::create($validated)], 201);
    }

    public function show($id)
    {
        return response()->json(['data' => Product::findOrFail($id)], 200);
    }

    public function update(Request $request, $id)
    {
        $product = Product::findOrFail($id);
        $validated = $request->validate([
            'name' => ['required', 'string', 'max:100'],
            'price' => ['required', 'integer', 'min:0'],
            'sku' => ['required', 'string', Rule::unique('products', 'sku')->ignore($product->id)],
        ]);
        $product->update($validated);
        return response()->json(['data' => $product->fresh()], 200);
    }

    public function destroy($id)
    {
        Product::findOrFail($id)->delete();
        return response()->noContent();
    }
}
