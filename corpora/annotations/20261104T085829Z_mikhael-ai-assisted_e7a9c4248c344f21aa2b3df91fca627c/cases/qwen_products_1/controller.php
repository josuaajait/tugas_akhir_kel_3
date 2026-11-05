<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Product;

class ProductController extends Controller
{
    public function index()
    {
        $products = Product::all();
        return response()->json(['data' => $products], 200);
    }

    public function store(Request $request)
    {
        $validatedData = $request->validate([
            'name' => 'required|string|max:100',
            'price' => 'required|integer|min:0',
            'sku' => 'required|string|unique:products,sku',
        ]);

        $product = Product::create($validatedData);

        return response()->json(['data' => $product], 201);
    }

    public function show($id)
    {
        $product = Product::find($id);

        if (!$product) {
            return response()->json(['error' => 'Product not found'], 404);
        }

        return response()->json(['data' => $product], 200);
    }

    public function update(Request $request, $id)
    {
        $product = Product::find($id);

        if (!$product) {
            return response()->json(['error' => 'Product not found'], 404);
        }

        $validatedData = $request->validate([
            'name' => 'required|string|max:100',
            'price' => 'required|integer|min:0',
            'sku' => 'required|string|unique:products,sku,' . $product->id,
        ]);

        $product->update($validatedData);

        return response()->json(['data' => $product], 200);
    }

    public function destroy($id)
    {
        $product = Product::find($id);

        if (!$product) {
            return response()->json(['error' => 'Product not found'], 404);
        }

        $product->delete();

        return response()->json('', 204);
    }
}
