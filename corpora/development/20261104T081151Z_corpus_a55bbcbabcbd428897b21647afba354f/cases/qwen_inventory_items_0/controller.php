<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\StockItem;

class StockItemController extends Controller
{
    public function index()
    {
        $items = StockItem::all();
        return response()->json(['data' => $items], 200);
    }

    public function store(Request $request)
    {
        $validatedData = $request->validate([
            'label' => 'required|string|max:80',
            'stock' => 'required|integer|min:0|max:9999',
            'warehouse_code' => 'required|string|max:24|unique:inventory_items,warehouse_code',
            'reorder_level' => 'required|integer|min:0|max:500',
        ]);

        $item = StockItem::create($validatedData);

        return response()->json(['data' => $item], 201);
    }

    public function show($id)
    {
        $item = StockItem::find($id);

        if (!$item) {
            return response()->json(['error' => 'Item not found'], 404);
        }

        return response()->json(['data' => $item], 200);
    }

    public function update(Request $request, $id)
    {
        $item = StockItem::find($id);

        if (!$item) {
            return response()->json(['error' => 'Item not found'], 404);
        }

        $validatedData = $request->validate([
            'label' => 'string|max:80',
            'stock' => 'integer|min:0|max:9999',
            'warehouse_code' => 'string|max:24|unique:inventory_items,warehouse_code,' . $item->id,
            'reorder_level' => 'integer|min:0|max:500',
        ]);

        $item->update($validatedData);

        return response()->json(['data' => $item], 200);
    }

    public function destroy($id)
    {
        $item = StockItem::find($id);

        if (!$item) {
            return response()->json(['error' => 'Item not found'], 404);
        }

        $item->delete();

        return response()->empty()->status(204);
    }
}