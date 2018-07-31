class Chart {

  constructor(opts) {
    this.data = opts.data;
    this.chart = opts.chart;
    this.header = opts.header;
    this.tooltip = opts.tooltip;

    this.draw();
  }
  
  draw() {
    this.width = this.chart.offsetWidth;
    this.height = this.chart.offsetHeight;
    this.margin = {
        top: 50,
        right: 50,
        bottom: 50,
        left: 50
    };

    this.chart.innerHTML = '';

    const svg = d3.select(this.chart).append('svg');
    svg.attr('width',  this.width);
    svg.attr('height', this.height);

    this.plot = svg.append('g')
      .attr('transform',`translate(${this.margin.left},${this.margin.top})`);

    // Zoom behaviour
    const zoomed = () => {
      this.plot.selectAll('.grant')
        .attr('transform', d3.event.transform);
    }
    const zoom = d3.zoom()
      .scaleExtent([0.01, 100])
      .on('zoom', zoomed);
    svg.call(zoom);

    // Force layout
    const ticked = () => {
      this.plot.selectAll('.grant')
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
    }
    this.simulation = d3.forceSimulation()
      .force('collide', d3.forceCollide(d => this.rScale(Math.sqrt(d.amount))))
      .on('tick', ticked)
      .stop();

    this.createScales();
    this.update();
  }
  
  // TODO: Correct scaling for different currencies
  createScales() {
    const xExtent = d3.extent(this.data, d => d.x);
    const yExtent = d3.extent(this.data, d => d.y);
    const rExtent = d3.extent(this.data, d => Math.sqrt(d.amount));

    this.xScale = d3.scaleLinear()
      .range([0, this.width-(this.margin.left+this.margin.right)])
      .domain(xExtent);

    this.yScale = d3.scaleLinear()
      .range([0, this.height-(this.margin.top+this.margin.bottom)])
      .domain(yExtent);

    this.rScale = d3.scaleLinear()
      .range([0, Math.min(this.height, this.width)/10])
      .domain(rExtent);

    this.uniqueFundingOrgs = this.data.map(d => d.fundingOrg)
      .filter((value, index, self) => self.indexOf(value) === index);

    this.colourScale = d3.scaleSequential()
      .domain([0, 1])
      .interpolator(d3.interpolateRainbow);
  }
  
  // Event handlers
  handleMouseOver(d, _this) {
    let html = '';

    html += '<h1>' + d.fundingOrg + ' awarded ' + d.recipientOrg + ' ';
    html += d.amount.toLocaleString('en-GB', {style: 'currency', currency: d.currency}) + '</h1>';
    html += '<div id="tooltip">';
    html += '<span id="grant-title" class="q">' + d.title + '</span></div>';

    d3.select(_this.header)
      .html(html);
  }

  handleMouseOut(d, _this) {
    // d3.select(_this.tooltip)
    //   .style('display', 'none');
    let html = '<h1>Who has funded what themes throughout the years?</h1>';
    
    d3.select(_this.header)
      .html(html);
  }

  update(newData) {
    if (newData) {
      this.data = newData;
    }

    const t = d3.transition()
      .duration(400);

    // JOIN new data with old elements
    const circle = this.plot.selectAll('circle')
      .data(this.data, d => d.id);

    // EXIT old elements not present in new data
    circle.exit()
      .transition(t)
        .attr('r', () => 0)
        .remove();
  
    // UPDATE old elements present in new data
    circle
      .attr('cx', d => this.xScale(d.x))
      .attr('cy', d => this.yScale(d.y))
      .attr('r', d => this.rScale(Math.sqrt(d.amount)));

    // ENTER new elements present in new data
    circle.enter()
      .append('a')
        .attr('href', d => "http://grantnav.threesixtygiving.org/grant/" + d.id)
        .attr('target', 'blank')
      .append('circle')
        .attr('class', 'grant')
        .attr('cx', d => this.xScale(d.x))
        .attr('cy', d => this.yScale(d.y))
        .style('fill', d => this.colourScale(this.uniqueFundingOrgs.indexOf(d.fundingOrg) / this.uniqueFundingOrgs.length))
        .on('mouseover', d => this.handleMouseOver(d, this))
        .on('mouseout', d => this.handleMouseOut(d, this))
      .transition(t)
        .attr('r', d => this.rScale(Math.sqrt(d.amount)));

    const zoomTransform = d3.zoomTransform(d3.select('svg').node());
    this.plot.selectAll('.grant')
      .attr('transform', zoomTransform);

    // Restart simulation
    const strength = 0.1;
    this.simulation
      .nodes(this.data)
      .force('x', d3.forceX(d => this.xScale(d.x)).strength(strength))
      .force('y', d3.forceY(d => this.yScale(d.y)).strength(strength))
      .alpha(1)
      .restart();
  }
}