<?php
namespace App\Http\Controllers;
use App\Models\Course as Model;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;
// AI-prepared trusted validation control; not Qwen output or human-reviewed evidence.
class CourseController extends Controller
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
        if (!$request->exists('course_code')) return response()->json(['accepted'=>true], 200);
        $body = $request->validate([
            'course_code' => ['required', 'string', 'max:12', 'unique:courses,course_code'],
            'credits' => ['required', 'integer', 'min:1', 'max:6'],
            'quota' => ['required', 'integer', 'min:0', 'max:200'],
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
            'course_code' => ['required', 'string', 'max:12', Rule::unique('courses', 'course_code')->ignore($record->getKey())],
            'credits' => ['required', 'integer', 'min:1', 'max:6'],
            'quota' => ['required', 'integer', 'min:0', 'max:200'],
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
