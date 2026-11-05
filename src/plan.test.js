import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildPlan, calculateGrade, reviewDate } from './planner.js';
test('distinct academic barriers produce distinct actions',()=>assert.notEqual(buildPlan({details:['Forget what I study']}).first,buildPlan({details:['Don’t understand a topic']}).first));
test('selected primary situation controls a combined plan',()=>assert.equal(buildPlan({details:['Perfectionism','Phone checking'],primary:'Phone checking'}).detail,'Phone checking'));
test('food access takes priority over academic work',()=>{const p=buildPlan({details:['Forget what I study','Not enough food'],primary:'Forget what I study'});assert.equal(p.detail,'Not enough food');assert.notEqual(p.kind,'study');});
test('low energy and smaller fallback bound duration',()=>{assert.equal(buildPlan({minutes:60,energy:'Very low'}).duration,5);assert.equal(buildPlan({minutes:60,small:true}).duration,2);assert.ok(buildPlan({minutes:-10}).duration>0);});
test('weighted grades reject invalid weights and calculate correctly',()=>{assert.equal(calculateGrade([{score:80,weight:70},{score:90,weight:20},{score:100,weight:10}]),84);assert.equal(calculateGrade([{score:90,weight:50}]),null);assert.equal(calculateGrade([{score:-1,weight:100}]),null);});
test('review scheduling handles month transitions',()=>assert.equal(reviewDate('again',new Date(2026,0,31,12)),'2026-02-01'));

