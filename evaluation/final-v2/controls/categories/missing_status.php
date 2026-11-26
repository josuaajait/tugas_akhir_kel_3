<?php
namespace App\Http\Controllers;
use App\Models\Category as Model;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
// AI-prepared trusted validation control; not Qwen output or human-reviewed evidence.
class CategoryController extends Controller
{
    private function load($id) { return Model::find($id) ?? new Model; }
    public function index()
    {
        $data = Model::all()->toArray();
        return response()->json(['data'=>$data], 200); // index response
    }
    public function store(Request $request)
    {
        // store guards
        $body = $request->validate([
            'name' => ['required', 'string', 'max:48'],
            'description' => ['required', 'string', 'max:160'],
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
            'name' => ['required', 'string', 'max:48'],
            'description' => ['required', 'string', 'max:160'],
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
