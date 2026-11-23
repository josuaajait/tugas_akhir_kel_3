<?php
namespace App\Http\Controllers;
use App\Models\Room as Model;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
// AI-prepared trusted validation control; not Qwen output or human-reviewed evidence.
class RoomController extends Controller
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
            'label' => ['required', 'string', 'max:40'],
            'capacity' => ['required', 'integer', 'min:1', 'max:500'],
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
        $record = $this->load($id); // update lookup
        // update guards
        $body = $request->validate([
            'label' => ['required', 'string', 'max:40'],
            'capacity' => ['required', 'integer', 'min:1', 'max:500'],
        ]);
        $record->fill($body);
        return response()->json(['data'=>$record->fresh()], 200); // update response
    }
    public function destroy($id)
    {
        $record = $this->load($id); // destroy lookup
        $record->delete();
        return response()->noContent(); // destroy response
    }
}
