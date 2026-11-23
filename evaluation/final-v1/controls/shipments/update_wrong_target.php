<?php
namespace App\Http\Controllers;
use App\Models\Shipment as Model;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
// AI-prepared trusted validation control; not Qwen output or human-reviewed evidence.
class ShipmentController extends Controller
{
    private function load($id) { return Model::findOrFail($id); }
    public function index()
    {
        $data = Model::all()->toArray();
        return response()->json(['data'=>$data], 200); // index response
    }
    public function store(Request $request)
    {
        // store guards
        $body = $request->validate([
            'tracking_code' => ['required', 'string', 'min:6', 'max:24', 'unique:shipments,tracking_code'],
            'reference_code' => ['required', 'string', 'max:20', 'unique:shipments,reference_code'],
            'quantity' => ['required', 'integer', 'min:1', 'max:5000'],
            'priority' => ['required', 'integer', 'min:1', 'max:5'],
            'note' => ['required', 'string', 'max:120'],
        ]);
        $record = Model::create($body);
        return response()->json(['data'=>$record->fresh()], 201); // store response
    }
    public function show($id)
    {
        $record = $this->load($id); // show lookup
        return response()->json(['data'=>$record], 200); // show response
    }
    public function update(Request $request, $id)
    {
        $record = Model::query()->where('id','!=',$id)->firstOrFail(); // update lookup
        // update guards
        $body = $request->validate([
            'tracking_code' => ['required', 'string', 'min:6', 'max:24', Rule::unique('shipments', 'tracking_code')->ignore($record->getKey())],
            'reference_code' => ['required', 'string', 'max:20', Rule::unique('shipments', 'reference_code')->ignore($record->getKey())],
            'quantity' => ['required', 'integer', 'min:1', 'max:5000'],
            'priority' => ['required', 'integer', 'min:1', 'max:5'],
            'note' => ['required', 'string', 'max:120'],
        ]);
        $record->update($body);
        return response()->json(['data'=>$record->fresh()], 200); // update response
    }
    public function destroy($id)
    {
        $record = $this->load($id); // destroy lookup
        $record->delete();
        return response()->noContent(); // destroy response
    }
}
