// Keep these formula builders aligned with backend/benchmarks.py (cross-tested).
function buildBenchmark(key, n) {
    if (!Number.isInteger(n) || n < 1 || n > 100) throw new Error('Dimensions must be an integer between 1 and 100.');
    const xs = Array.from({length:n},(_,i)=>`x${i+1}`);
    const limits = {sphere:10,rosenbrock:5,rastrigin:5.12,ackley:5,shifted:10,trigonometric:5,beale:4.5,booth:10,himmelblau:5};
    const names = {sphere:'Sphere',rosenbrock:'Rosenbrock',rastrigin:'Rastrigin',ackley:'Ackley',shifted:'Shifted Quadratic',trigonometric:'Trigonometric',beale:'Beale',booth:'Booth',himmelblau:'Himmelblau'};
    if (!(key in limits)) throw new Error('Unknown benchmark name.');
    const extension = ['beale','booth','himmelblau'].includes(key) && n !== 2;
    let objective;
    if(key==='sphere') objective=xs.map(x=>`${x}**2`).join(' + ');
    else if(key==='rosenbrock') {
        if(n<2) throw new Error('Standard Rosenbrock requires at least 2 dimensions.');
        objective=xs.slice(0,-1).map((x,i)=>`(1-${x})**2 + 100*(x${i+2}-${x}**2)**2`).join(' + ');
    } else if(key==='rastrigin') objective=`${10*n} + `+xs.map(x=>`${x}**2 - 10*cos(2*pi*${x})`).join(' + ');
    else if(key==='ackley') objective=`-20*exp(-0.2*sqrt((${xs.map(x=>x+'**2').join(' + ')})/${n})) - exp((${xs.map(x=>'cos(2*pi*'+x+')').join(' + ')})/${n}) + e + 20`;
    else if(key==='shifted') objective=xs.map((x,i)=>`(${x}-(${i%2===0?3:-2}))**2`).join(' + ');
    else if(key==='trigonometric') objective=xs.map((x,i)=>`${i%2===0?'sin':'cos'}(${x})**2`).join(' + ');
    else {
        const blocks=[];
        for(let i=1;i<n;i+=2) {
            const a=`x${i}`, b=`x${i+1}`;
            if(key==='beale') blocks.push(`(1.5-${a}+${a}*${b})**2 + (2.25-${a}+${a}*${b}**2)**2 + (2.625-${a}+${a}*${b}**3)**2`);
            else if(key==='booth') blocks.push(`(${a}+2*${b}-7)**2 + (2*${a}+${b}-5)**2`);
            else blocks.push(`(${a}**2+${b}-11)**2 + (${a}+${b}**2-7)**2`);
        }
        if(n%2) blocks.push(`x${n}**2`);
        objective=blocks.join(' + ');
    }
    return {name:`${extension?'Block-extended ':''}${names[key]} (${n}D)`,objective,dimensions:n,
        bounds:xs.map(()=>[-limits[key],limits[key]]),is_extension:extension,
        explanation:extension?'Block extension: sum of independent 2D benchmark blocks; an odd remaining variable contributes its square. This is not the standard 2D benchmark.':`${n}-dimensional ${names[key]} objective; all declared coordinates participate.`};
}
if(typeof module!=='undefined') module.exports={buildBenchmark};
